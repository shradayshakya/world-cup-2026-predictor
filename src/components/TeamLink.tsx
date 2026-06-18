import Link from "next/link";
import { slugify } from "@/lib/slug";

export default function TeamLink({ name, className }: { name: string; className?: string }) {
  return (
    <Link href={`/teams/${slugify(name)}`} className={className ?? "hover:underline"}>
      {name}
    </Link>
  );
}
