/*
 * This component renders a simple button with an onclick action
 */
import { Link } from "preact-router/match";
import cn from "classnames";

type Props = {
    label: string | Element;
    disabled?: boolean;
    href?: string;
    onClick?: () => void;
};

const Button = ({ label, disabled, href, onClick }: Props) => (
    <Link
        href={href}
        onClick={onClick}
        disabled={disabled}
        className={cn(
            "text-white font-bold py-2 px-4 rounded",
            { "cursor-not-allowed bg-gray-500": disabled },
            { "cursor-pointer bg-blue-500 hover:bg-blue-600": !disabled }
        )}>
        {label}
    </Link>
);
export default Button;
