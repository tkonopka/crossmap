import React from 'react';
import List from '@material-ui/core/List';
import ChatUserMessage from './ChatUserMessage';
import ChatServerMessage from "./ChatServerMessage";


class ChatHistory extends React.Component {

    componentDidUpdate () {
        if (this.chatEndMarker !== null) {
            this.chatEndMarker.scrollIntoView({behavior: "smooth"})
        }
    }

    render() {
        let messages = this.props.messages.map(function (x, i) {
            if (x[0] === "user") {
                return (<ChatUserMessage key={i} data={x[1]}/>)
            } else {
                return (<ChatServerMessage key={i} data={x[1]}/>)
            }
        });
        let liststyle = {"height": this.props.height, "position": 0, "width": "auto"};
        return (<List id="chat-history" style={liststyle}>
                    {messages}
                    <div ref={(divElement)=> this.chatEndMarker = divElement} className={"chat-end"}></div>
                </List>);
    }
}


export default ChatHistory;