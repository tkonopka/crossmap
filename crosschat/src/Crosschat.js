import React from 'react';
import ChatInit from './ChatInit';
import Controller from "./Controller";
import ChatHistory from "./ChatHistory";


class Crosschat extends React.Component {
    constructor(props) {
        super(props);
        this.addMessage= this.addMessage.bind(this);
        this.sendQuery = this.sendQuery.bind(this);
        this.state = {history: [], datasets: []}
    }

    /**
     * when the component first mounts, request summary information from the API
     */
    componentDidMount() {
        console.log("componentDidMount")
        const chat = this;
        let xhr = new XMLHttpRequest();
        xhr.onload = function() {
            console.log("received: "+xhr.response);
            let result = JSON.parse(xhr.response);
            result["_type"] = "datasets";
            chat.addMessage(result, "server")
            chat.setState({history: [["server", result]],
                           datasets: result["datasets"]})
        };
        xhr.open("POST", "http://127.0.0.1:8098/datasets/", true);
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send();
    }

    /**
     * submit a query to the server
     * @param query object, payload sent to the api
     * @param api character, api endpoint, e.g. "predict/" or "decompose/"
     */
    sendQuery(query, api) {
        // augment the query with settings
        console.log("Sending to api: "+ api);
        console.log("query: "+JSON.stringify(query));
        const chat = this;
        chat.addMessage(query, "user");
        let xhr = new XMLHttpRequest();
        xhr.onload = function(){
            let result = JSON.parse(xhr.response);
            console.log("got response: "+JSON.stringify(result));
            result["_type"] = api;
            console.log("edited response: "+JSON.stringify(result));
            chat.addMessage(result, "server")
        };
        xhr.open("POST", "http://127.0.0.1:8098/" + api + "/", true);
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(query));
    }

    /**
     * Add a box into the chat history to record user interaction and server response
     *
     * @param message object
     * @param type string, typically "user" or "server" to distinguish two sides
     * of a chat
     */
    addMessage(message, type) {
        this.setState(prevState => {
            const history = prevState.history.concat([[type, message]]);
            return {history: history}
        });
    }

    render() {
        if (this.state.history.length === 0) {
            return (<ChatInit />)
        }
        return(
            <div className="crosschat">
                <ChatHistory messages={this.state.history} />
                <Controller datasets={this.state.datasets} send={this.sendQuery}/>
            </div>
        )
    }
}

export default Crosschat;