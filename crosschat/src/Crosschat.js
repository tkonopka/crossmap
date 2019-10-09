import React from 'react';
import ChatInit from './ChatInit';
import ChatController from "./ChatController";
import ChatHistory from "./ChatHistory";


class Crosschat extends React.Component {
    constructor(props) {
        super(props);
        this.addMessage= this.addMessage.bind(this);
        this.predictQuery = this.predictQuery.bind(this);
        this.decomposeQuery = this.decomposeQuery.bind(this);
        this.state = {history: [], datasets: []}
    }

    addMessage(message, type) {
        this.setState(prevState => {
            const history = prevState.history.concat([[type, message]]);
            return {history: history}
        });
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
        query["dataset"] = "targets";
        query["n"] = 3;
        query["aux"] = {};
        const chat = this;
        chat.addMessage(query, "user");
        let xhr = new XMLHttpRequest();
        xhr.onload=function(){
            chat.addMessage(JSON.parse(xhr.response), "server")
        };
        xhr.open("POST", "http://127.0.0.1:8098/" + api, true);
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(query));
    }
    /** two wrappers for sendQuery to predict and decompose a user's data **/
    predictQuery = (query) => this.sendQuery(query, "predict/");
    decomposeQuery = (query) => this.sendQuery(query, "decompose/");

    render() {
        if (this.state.history.length === 0) {
            return (<ChatInit />)
        }
        return(
            <div className="crosschat">
                <ChatHistory messages={this.state.history} />
                <ChatController datasets={this.state.datasets}/>
            </div>
        )
    }
}

export default Crosschat;