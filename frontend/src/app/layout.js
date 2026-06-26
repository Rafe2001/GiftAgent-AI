'use client';
import "./globals.css";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function RootLayout({ children }) {
  const pathname = usePathname();

  const navLinks = [
    { href: "/", label: "Dashboard", icon: "📊" },
    { href: "/upload", label: "Upload", icon: "📤" },
  ];

  return (
    <html lang="en">
      <head>
        <title>Gift Recommendation Agent</title>
        <meta name="description" content="AI-powered hyper-personalised gift recommendation system for professional contacts" />
      </head>
      <body>
        <nav className="navbar">
          <div className="navbar-inner">
            <Link href="/" className="navbar-brand">
              <span className="logo-icon">🎁</span>
              <span>GiftAgent AI</span>
            </Link>
            <div className="navbar-links">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`nav-link ${pathname === link.href ? "active" : ""}`}
                >
                  {link.icon} {link.label}
                </Link>
              ))}
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
