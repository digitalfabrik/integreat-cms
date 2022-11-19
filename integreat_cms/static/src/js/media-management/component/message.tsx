/*
 * This component renders a success or error message and removes it after 10 seconds
 */
import { useEffect, useState } from "preact/hooks";
import cn from "classnames";

export type Message = {
    type: string;
    text: string;
};

type Props = {
    newMessage: Message;
};

const MessageComponent = ({ newMessage }: Props) => {
    // This state contains the current success or error message
    const [messageQueue, setMessagesQueue] = useState<Message[]>([]);
    // This state is a trigger to remove the first message from the message queue
    const [hideMessage, setHideMessage] = useState<boolean>(false);

    useEffect(() => {
        // When hideMessage gets triggered, remove the first element from the message queue
        if (hideMessage) {
            setMessagesQueue((mq) => mq.slice(1));
            setHideMessage(false);
        }
    }, [hideMessage]);

    useEffect(() => {
        if (newMessage) {
            // Add message to message queue
            setMessagesQueue((mq) => mq.concat(newMessage));
            // Remove message after 10 seconds
            const removalTimeout = 10_000;
            setTimeout(() => setHideMessage(true), removalTimeout);
        }
    }, [newMessage]);

    // Assign unique key per message to optimize preact rendering
    return (
        <div>
            {messageQueue.map((message) => (
                <div
                    key={window.btoa(message.text)}
                    className={cn(
                        "border-l-4 px-4 py-3 mb-4 break-all",
                        { "bg-green-100 border-green-500 text-green-500": message.type === "success" },
                        { "bg-blue-100 border-blue-500 text-blue-500": message.type === "info" },
                        { "bg-orange-100 border-orange-500 text-orange-500": message.type === "warning" },
                        { "bg-red-100 border-red-500 text-red-500": message.type === "error" }
                    )}
                    role="alert">
                    {message.text}
                </div>
            ))}
        </div>
    );
};
export default MessageComponent;
