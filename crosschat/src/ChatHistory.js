import React from 'react';
import ChatUserMessage from './ChatUserMessage';
import ChatServerMessage from "./ChatServerMessage";


class ChatHistory extends React.Component {
    render() {
        console.log("----- Chat History render ------");
        let messages = this.props.messages.map(function (x, i) {
            if (x[0] === "user") {
                return (<ChatUserMessage key={i} data={x[1]}/>)
            } else {
                return (<ChatServerMessage key={i} data={x[1]}/>)
            }
        });
        return (<ul className='chat-list' >{messages}</ul>);
    }
}


export default ChatHistory;