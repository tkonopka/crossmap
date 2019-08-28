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
                return (<tbody key={i}><tr><td>{x}</td><td>{dists[i]}</td></tr></tbody>)
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
                return (<tbody key={i}><tr><td>{x}</td><td>{coeffs[i]}</td></tr></tbody>)
            });
            return (
                <div className="chat-response">
                <table>
                    <tbody><tr><th>target</th><td>coefficient</td></tr></tbody>
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
        return (
            <div className="chat-user">
                <table><tbody>
                    <tr><td>data</td><td>{this.props.data["data"]}</td></tr>
                    <tr><td>aux_pos</td><td>{this.props.data["aux_pos"]}</td></tr>
                    <tr><td>aux_neg</td><td>{this.props.data["aux_neg"]}</td></tr>
                </tbody></table>
            </div>
        )
    }
}

class CrosschatHistory extends React.Component {
    render() {
        //console.log("history: "+JSON.stringify(this.props.messages));
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
                <button className="button" onClick={(e) => this.props.predictQuery(e, this.state)}>Predict</button>
                <button className="button" onClick={(e) => this.props.decomposeQuery(e, this.state)}>Decompose</button>
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

    /** submit a query to the server **/
    predictQuery(e, query) {
        const chat = this;
        chat.addMessage(query, "user");
        let xhr = new XMLHttpRequest();
        xhr.onload=function(){
            //console.log(xhr.response);
            chat.addMessage(JSON.parse(xhr.response), "server")
        };
        xhr.open("POST","http://127.0.0.1:8098/predict/", true);
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.setRequestHeader('Content-Type', 'application/json');
        query["n_targets"] = 3;
        query["n_documents"] = 3;
        xhr.send(JSON.stringify(query));
    }
    decomposeQuery(e, query) {
        console.log("Decomposition with "+JSON.stringify(query))
    }

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
