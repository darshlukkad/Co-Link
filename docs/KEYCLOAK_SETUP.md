# Keycloak SSO Setup Guide

Complete guide for configuring Keycloak with Google and GitHub OIDC providers, plus TOTP 2FA.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Starting Keycloak](#starting-keycloak)
- [Initial Keycloak Configuration](#initial-keycloak-configuration)
- [Google OAuth Setup](#google-oauth-setup)
- [GitHub OAuth Setup](#github-oauth-setup)
- [Enabling 2FA (TOTP)](#enabling-2fa-totp)
- [Testing Authentication](#testing-authentication)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose installed
- Google account (for Google OAuth)
- GitHub account (for GitHub OAuth)
- Access to Google Cloud Console
- Access to GitHub Developer Settings

## Starting Keycloak

### 1. Start Infrastructure

```bash
# Start all infrastructure services
docker-compose -f docker-compose.dev.yml up -d

# Wait for Keycloak to be ready (takes ~30-60 seconds)
docker-compose logs -f keycloak
```

Wait for the message: `Running the server in development mode`

### 2. Access Keycloak Admin Console

- URL: http://localhost:8080
- Username: `admin`
- Password: `admin` (development only!)

The `colink` realm should be auto-imported on first startup.

## Initial Keycloak Configuration

### Verify Realm Import

1. Click on the realm dropdown (top-left)
2. Verify `colink` realm exists
3. Switch to `colink` realm

### Verify Clients

Navigate to **Clients** → should see:
- `colink-web` - Public client for React frontend
- `colink-api` - Confidential client for backend services

## Google OAuth Setup

### Step 1: Create Google OAuth Client

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing: **CoLink**
3. Enable **Google+ API** (if not already enabled)
4. Navigate to **APIs & Services** → **Credentials**
5. Click **Create Credentials** → **OAuth 2.0 Client ID**
6. Configure OAuth consent screen (if first time):
   - User Type: **External** (or Internal for G Suite)
   - App name: **CoLink**
   - User support email: your email
   - Developer contact: your email
   - Add scopes: `email`, `profile`, `openid`
   - Add test users (for development)

7. Create OAuth Client ID:
   - Application type: **Web application**
   - Name: **CoLink Development**
   - Authorized JavaScript origins:
     - `http://localhost:8080`
   - Authorized redirect URIs:
     - `http://localhost:8080/realms/colink/broker/google/endpoint`
   - Click **Create**

8. **Copy the Client ID and Client Secret** (you'll need these)

### Step 2: Configure Google in Keycloak

1. In Keycloak Admin Console, navigate to:
   - **Identity Providers** → **Add provider** → **Google**

2. Fill in the configuration:
   - **Alias**: `google` (must match)
   - **Display Name**: `Google`
   - **Enabled**: ON
   - **Store Tokens**: OFF (recommended)
   - **Stored Tokens Readable**: OFF
   - **Trust Email**: ON
   - **First Login Flow**: `first broker login`
   - **Client ID**: *paste from Google Console*
   - **Client Secret**: *paste from Google Console*
   - **Default Scopes**: `openid profile email`

3. Click **Save**

4. **Important**: Copy the **Redirect URI** shown at the top
   - Should be: `http://localhost:8080/realms/colink/broker/google/endpoint`
   - Go back to Google Cloud Console and verify this is in **Authorized redirect URIs**

### Step 3: Test Google Login

1. Open http://localhost:8080/realms/colink/account
2. Click **Sign in with Google**
3. Authenticate with your Google account
4. Should redirect back to Keycloak account page

## GitHub OAuth Setup

### Step 1: Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in the form:
   - **Application name**: CoLink Development
   - **Homepage URL**: `http://localhost:5173`
   - **Authorization callback URL**:
     - `http://localhost:8080/realms/colink/broker/github/endpoint`
   - Click **Register application**

4. **Copy the Client ID**
5. Click **Generate a new client secret**
6. **Copy the Client Secret** (only shown once!)

### Step 2: Configure GitHub in Keycloak

1. In Keycloak Admin Console, navigate to:
   - **Identity Providers** → **Add provider** → **GitHub**

2. Fill in the configuration:
   - **Alias**: `github` (must match)
   - **Display Name**: `GitHub`
   - **Enabled**: ON
   - **Store Tokens**: OFF
   - **Stored Tokens Readable**: OFF
   - **Trust Email**: OFF (GitHub emails may not be verified)
   - **First Login Flow**: `first broker login`
   - **Client ID**: *paste from GitHub*
   - **Client Secret**: *paste from GitHub*
   - **Default Scopes**: `user:email`

3. Click **Save**

4. **Verify Redirect URI** matches what you entered in GitHub:
   - `http://localhost:8080/realms/colink/broker/github/endpoint`

### Step 3: Test GitHub Login

1. Open http://localhost:8080/realms/colink/account
2. Click **Sign in with GitHub**
3. Authorize the app (first time)
4. Should redirect back to Keycloak

## Enabling 2FA (TOTP)

2FA is already configured in the realm import but here's how to verify and customize:

### Verify OTP Policy

1. Navigate to **Authentication** → **Policies** → **OTP Policy**
2. Verify settings:
   - **OTP Type**: Time-based
   - **OTP Hash Algorithm**: SHA256
   - **Number of Digits**: 6
   - **OTP Token Period**: 30 seconds
   - **Look-ahead Window**: 1

### Configure Required Actions

1. Navigate to **Authentication** → **Required Actions**
2. Ensure **Configure OTP** is:
   - **Enabled**: ON
   - **Default Action**: ON

This forces all users to set up TOTP on first login.

### Supported Authenticator Apps

- Google Authenticator (iOS/Android)
- Microsoft Authenticator (iOS/Android)
- FreeOTP (iOS/Android)
- Authy (iOS/Android/Desktop)
- 1Password
- Bitwarden

### Test 2FA Setup

1. Create a new user or login with existing account
2. After initial authentication, you'll be prompted to configure TOTP
3. Scan the QR code with your authenticator app
4. Enter the 6-digit code
5. 2FA is now required for all future logins

## Testing Authentication

### Test with cURL

```bash
# Get access token (password grant - requires user credentials)
curl -X POST "http://localhost:8080/realms/colink/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=colink-api" \
  -d "client_secret=colink-api-secret-dev-only" \
  -d "username=testuser" \
  -d "password=testpass" \
  -d "grant_type=password"

# Response includes access_token, refresh_token, id_token
```

### Test with Frontend

```javascript
// Using Keycloak JavaScript adapter
import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: 'http://localhost:8080',
  realm: 'colink',
  clientId: 'colink-web'
});

keycloak.init({ onLoad: 'login-required' }).then(authenticated => {
  if (authenticated) {
    console.log('Authenticated!');
    console.log('Token:', keycloak.token);
  }
});
```

### Test with API Gateway

```bash
# Get token first (via browser or curl)
TOKEN="your-jwt-token-here"

# Call protected endpoint
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# Should return user info
```

## Environment Variables

Update `.env` file with your OAuth credentials:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-google-client-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

## Production Configuration

### For Production Deployment

1. **Use HTTPS everywhere**:
   - Keycloak: `https://auth.colink.com`
   - Frontend: `https://colink.com`
   - API: `https://api.colink.com`

2. **Update redirect URIs**:
   - Google Console: Add `https://auth.colink.com/realms/colink/broker/google/endpoint`
   - GitHub: Add `https://auth.colink.com/realms/colink/broker/github/endpoint`

3. **Enable SSL Required**: In Keycloak realm settings:
   - SSL required: **all requests**

4. **Secure secrets**:
   - Use AWS Secrets Manager or Kubernetes Secrets
   - Never commit secrets to Git
   - Rotate client secrets regularly

5. **Configure email**:
   - Update SMTP settings for password reset
   - Verify sender domain (SPF, DKIM)

6. **Session settings**:
   - SSO Session Idle: 30 minutes
   - SSO Session Max: 10 hours
   - Access Token Lifespan: 5-15 minutes
   - Refresh Token: 30 minutes

## Troubleshooting

### Issue: "Redirect URI mismatch"

**Solution**: Verify redirect URIs in Google/GitHub exactly match Keycloak's broker endpoint.

Google/GitHub redirect URI must be:
```
http://localhost:8080/realms/colink/broker/{google|github}/endpoint
```

### Issue: "Invalid client credentials"

**Solution**:
- Verify Client ID and Client Secret are correct
- Ensure no extra whitespace when copying
- Re-generate client secret if needed

### Issue: "TOTP not working"

**Solution**:
- Check device time is synchronized (TOTP is time-based)
- Verify OTP period is 30 seconds
- Try next code if timing is off
- Increase look-ahead window to 2-3

### Issue: "User not created after social login"

**Solution**:
- Check "First Login Flow" is set to `first broker login`
- Verify user registration is allowed (Realm Settings → Login)
- Check Keycloak logs: `docker-compose logs keycloak`

### Issue: "Token verification fails in API"

**Solution**:
- Verify `KEYCLOAK_URL` in `.env` matches container network
- Check Keycloak is accessible from API container
- Verify realm name matches exactly (`colink`)
- Check JWT issuer claim matches: `http://localhost:8080/realms/colink`

### View Keycloak Logs

```bash
# Follow Keycloak logs
docker-compose logs -f keycloak

# Search for errors
docker-compose logs keycloak | grep ERROR
```

### Reset Keycloak Data

```bash
# Stop and remove containers + volumes
docker-compose down -v

# Start fresh
docker-compose up -d

# Realm will be re-imported automatically
```

## Security Best Practices

1. **Never use default passwords in production**
2. **Enable brute force protection** (already enabled in realm)
3. **Require email verification** for new users
4. **Enable 2FA for all admin accounts**
5. **Regularly rotate secrets and tokens**
6. **Monitor login attempts** via Keycloak events
7. **Use strong password policies**
8. **Limit refresh token lifetime**
9. **Implement proper logout flows**
10. **Regular security updates** for Keycloak

## Additional Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [GitHub OAuth Apps](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [TOTP RFC 6238](https://tools.ietf.org/html/rfc6238)

## Support

For issues:
1. Check Keycloak logs
2. Verify environment variables
3. Test with Keycloak's built-in account console
4. Review this guide's troubleshooting section
5. Open an issue on GitHub with logs and configuration (redact secrets!)
