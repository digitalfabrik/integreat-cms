import { Link } from "preact-router/match";
interface Props {
  label: string;
  disabled?: boolean;
  href?: string;
  onClick?: () => void;
}

export default function Button({ label, disabled, href, onClick }: Props) {
  return (
    <Link
      href={href}
      onClick={onClick}
      disabled={disabled}
      class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline mr-2 cursor-pointer"
    >
      {label}
    </Link>
  );
}
