import React from 'react';


/**
 * A chat message class.
 * This is meant to capture some behaviors common to all messages
 *
 * **/
class ChatMessage extends React.Component {
    constructor(props) {
        super(props);
        this.handleMouseEnter = this.handleMouseEnter.bind(this);
        this.handleMouseLeave = this.handleMouseLeave.bind(this);
        this.state = {mouseover: 0}
    }

    handleMouseEnter() {
        this.setState({mouseover: 1})
    }
    handleMouseLeave() {
        this.setState({mouseover: 0})
    }

}


export default ChatMessage;