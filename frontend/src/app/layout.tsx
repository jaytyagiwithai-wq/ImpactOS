import type { Metadata } from "next";
import { MotionConfig } from "framer-motion";
import "./shadcn.css";
import "./globals.css";
import "./public-dark.css";
import "./product-demos.css";

export const metadata: Metadata = {
  title: {
    default: "ImpactOS — Know what follows the change",
    template: "%s · ImpactOS",
  },
  description:
    "Investigate an API change, trace its dependencies, and bring the evidence into view.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>
        <MotionConfig reducedMotion="user">{children}</MotionConfig>
      </body>
    </html>
  );
}
