import React from 'react';


/** a chat message with information provided by a user **/
class ChatUserMessage extends React.Component {
    render() {
        let data = this.props.data;
        let rows = ["data", "aux_pos", "aux_neg"].map((x) => {
            if (data[x]!== "") {
                return(<tr key={x}><td className="chat-td-label">{x}</td><td>{data[x]}</td></tr>)
            }
            return null;
        });
        return (
            <div className="chat-user">
                <table><tbody>{rows}</tbody></table>
            </div>
        )
    }
}


export default ChatUserMessage;