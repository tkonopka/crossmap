import React from 'react';
import Box from '@material-ui/core/Box';
import ChatInit from './ChatInit';
import Controller from "./Controller";
import ChatHistory from "./ChatHistory";


class Crosschat extends React.Component {
    constructor(props) {
        super(props);
        this.addMessage= this.addMessage.bind(this);
        this.sendQuery = this.sendQuery.bind(this);
        this.onresize = this.onresize.bind(this);
        this.state = {history: [], datasets: [],
                      chatHeight: '400', controllerHeight: 0}
        window.addEventListener('resize', this.onresize)
    }

    /**
     * when the component first mounts, request summary information from the API
     */
    componentDidMount() {
        console.log("crosschat componentDidMount");
        //this.setState({chatHeight: chatHeight});
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


    /** this is called from the controller to resize the chat/controller boxes **/
    onresize(controllerHeight) {
        // avoid setState when not needed to avoid infinite cycles of updates
        if (this.chatElement === null) {
            return;
        }
        if (!controllerHeight | typeof(controllerHeight) !== "number") {
            controllerHeight = this.state.controllerHeight;
        }
        let chatHeight = parseInt(this.chatElement.clientHeight);
        if (controllerHeight !== this.state.controllerHeight | chatHeight !== this.state.chatHeight) {
            this.setState({controllerHeight: controllerHeight, chatHeight: chatHeight});
        }
    }

    render() {
        if (this.state.history.length === 0) {
            return (<ChatInit />)
        }
        return(<Box id="chat" ref={(divElement) => this.chatElement = divElement}>
                <ChatHistory
                    height={this.state.chatHeight-this.state.controllerHeight}
                    messages={this.state.history} />
                <Controller
                    datasets={this.state.datasets}
                    onresize={this.onresize}
                    send={this.sendQuery}/>
        </Box>)
    }
}

export default Crosschat;