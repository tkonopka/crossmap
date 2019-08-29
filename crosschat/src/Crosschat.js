import React from 'react';
import './crosschat.css';


/** a chat message with a response provided by the server **/
class CrosschatServerMessage extends React.Component {
    render() {
        if (this.props.data["distances"] !== undefined) {
            let dists = this.props.data["distances"].map((x) => {
                return Number.parseFloat(x).toPrecision(4);
            });
            let rows = this.props.data["targets"].map(function(x, i) {
                return (<tbody key={i}><tr><td>{x}</td><td className="chat-td-numeric">{dists[i]}</td></tr></tbody>)
            });
            return (
                <div className="chat-response">
                <table>
                    <tbody><tr><th>target</th><th>distance</th></tr></tbody>
                    {rows}
                </table>
                </div>
            )
        } else {
            let coeffs = this.props.data["coefficients"].map((x) => {
                return Number.parseFloat(x).toPrecision(4);
            });
            let rows = this.props.data["targets"].map(function(x, i) {
                return (<tbody key={i}><tr><td>{x}</td><td className="chat-td-numeric">{coeffs[i]}</td></tr></tbody>)
            });
            return (
                <div className="chat-response">
                <table>
                    <tbody><tr><th>target</th><th>coefficient</th></tr></tbody>
                    {rows}
                </table>
                </div>
            )
        }
    }
}

/** a chat message with information provided by a user **/
class CrosschatUserMessage extends React.Component {
    render() {
        let data = this.props.data
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


class CrosschatHistory extends React.Component {
    render() {
        let messages = this.props.messages.map(function (x, i) {
            if (x[0] === "user") {
                return (<CrosschatUserMessage key={i} data={x[1]}/>)
            } else {
                return (<CrosschatServerMessage key={i} data={x[1]}/>)
            }
        });
        return (<ul className='chat-list' >{messages}</ul>);
    }
}


/**
 * widget with input boxes that allows user to type data and send
 * instruction to the server
 */
class CrosschatQueryBox extends React.Component {
    constructor(props) {
        super(props);
        this.setText = this.setText.bind(this);
        this.state = {data: "", aux_pos: "", aux_neg: ""}
    }

    /** transfer content of textbox into object state **/
    setText(e, key) {
        let obj = {};
        obj[key] = e.target.value;
        this.setState(obj);
    }

    render() {
        return(
            <div className="chat-query">
                <textarea type='text' placeholder="Data" onInput={(e) => this.setText(e, "data")}/>
                <textarea type='text' placeholder="Aux pos" onInput={(e) => this.setText(e, "aux_pos")}/>
                <textarea type='text' placeholder="Aux neg" onInput={(e) => this.setText(e, "aux_neg")}/>
                <button className="button" onClick={() => this.props.predictQuery(this.state)}>Predict</button>
                <button className="button" onClick={() => this.props.decomposeQuery(this.state)}>Decompose</button>
            </div>
        )
    }
}

class Crosschat extends React.Component {
    constructor(props) {
        super(props);
        this.addMessage= this.addMessage.bind(this);
        this.predictQuery = this.predictQuery.bind(this);
        this.decomposeQuery = this.decomposeQuery.bind(this);
        this.state = {history: []}
    }

    addMessage(message, type) {
        this.setState(state => {
            const history = state.history.concat([[type, message]]);
            return {history: history}
        });
    }

    /**
     * submit a query to the server
     * @param query object, payload sent to the api
     * @param api character, api endpoint, e.g. "predict/" or "decompose/"
     */
    sendQuery(query, api) {
        // augment the query with settings
        query["n_targets"] = 3;
        query["n_documents"] = 3;
        const chat = this;
        chat.addMessage(query, "user");
        let xhr = new XMLHttpRequest();
        xhr.onload=function(){
            chat.addMessage(JSON.parse(xhr.response), "server")
        };
        xhr.open("POST","http://127.0.0.1:8098/" + api, true);
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(query));
    }
    /** two wrappers for sendQuery to predict and decompose a user's data **/
    predictQuery = (query) => this.sendQuery(query, "predict/");
    decomposeQuery = (query) => this.sendQuery(query, "decompose/");

    render() {
        return(
            <div className="crosschat">
                <CrosschatHistory messages={this.state.history} />
                <CrosschatQueryBox predictQuery={this.predictQuery} decomposeQuery={this.decomposeQuery}/>
            </div>
        )
    }
}

export default Crosschat;
