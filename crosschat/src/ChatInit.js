import React from 'react';



/** A box used upon first initialization **/
class ChatInit extends React.Component {
    constructor(props) {
        super(props);
        this.state = { t: 0 }
    }

    /** didMound and WillUnmount implement a mechanism to change
     * the user message from "initializing" to "something went wrong"
     */
    componentDidMount() {
        this.interval = setInterval(
            () => this.setState({abandon: true}),
            10*1000
        );
    }
    componentWillUnmount() {
        clearInterval(this.interval);
    }

    render() {
        let message = "Initializing...";
        if (this.state.abandon) {
            message = "Something went wrong - check connection to server"
        }
        return(<div id="init-message">{ message }</div>)
    }
}

export default ChatInit;

