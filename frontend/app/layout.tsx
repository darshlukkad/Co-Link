import type { Metadata } from "next";
import "./globals.css";

// Font loading is optional - falls back to system fonts defined in globals.css
// Uncomment when building in an environment with internet access:
// import { Lato } from "next/font/google";
// const lato = Lato({
//   weight: ['300', '400', '700', '900'],
//   subsets: ["latin"],
//   variable: "--font-lato",
//   display: 'swap',
// });

export const metadata: Metadata = {
  title: "CoLink - Enterprise Team Collaboration",
  description: "A Slack-like real-time messaging platform for modern teams",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
