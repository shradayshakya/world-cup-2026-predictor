import Link from "next/link";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/bracket", label: "Bracket" },
  { href: "/groups", label: "Groups" },
  { href: "/scorers", label: "Scorers" },
  { href: "/about", label: "About" },
];

export default function NavBar() {
  return (
    <nav className="flex items-center gap-6 border-b border-neutral-200 px-4 py-3 sm:px-8">
      <span className="font-semibold tracking-tight">WC26 Predictor</span>
      <div className="flex gap-4 text-sm text-neutral-600">
        {LINKS.map((link) => (
          <Link key={link.href} href={link.href} className="hover:text-neutral-900 hover:underline">
            {link.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
