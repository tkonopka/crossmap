import React from 'react';
import Box from '@material-ui/core/Box';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import Typography from '@material-ui/core/Typography';


/** a chat message with a response provided by the server **/
class ChatServerMessageOld extends React.Component {
    render() {
        let titles = this.props.data["titles"];
        if (this.props.data["distances"] !== undefined) {
            let dists = this.props.data["distances"].map((x) => {
                return Number.parseFloat(x).toPrecision(4);
            });
            let rows = this.props.data["targets"].map(function(x, i) {
                return (<tbody key={i}><tr>
                    <td>{x}</td>
                    <td>{titles[i]}</td>
                    <td className="chat-td-numeric">{dists[i]}</td>
                </tr></tbody>)
            });
            return (
                <div className="chat-response">
                <table>
                    <tbody><tr><th>target</th><th>title</th><th>distance</th></tr></tbody>
                    {rows}
                </table>
                </div>
            )
        } else {
            let coeffs = this.props.data["coefficients"].map((x) => {
                return Number.parseFloat(x).toPrecision(4);
            });
            let rows = this.props.data["targets"].map(function(x, i) {
                return (<tbody key={i}><tr>
                    <td>{x}</td>
                    <td>{titles[i]}</td>
                    <td className="chat-td-numeric">{coeffs[i]}</td>
                </tr></tbody>)
            });
            return (
                <div className="chat-response">
                <table>
                    <tbody><tr><th>target</th><th>title</th><th>coefficient</th></tr></tbody>
                    {rows}
                </table>
                </div>
            )
        }
    }
}


class DatasetsMessage extends React.Component {
    render() {
        console.log(JSON.stringify(this.props.data));
        let datasets = this.props.data.map((x, i) => {
            return(
                <ListItem key={i}>
                <ListItemText primary={x["label"]} secondary={x["size"] + " items"}/>
                </ListItem>
            )
        })
        return(<Box>
            <Typography variant="h6">Available Datasets</Typography>
            <List>{datasets}</List>
        </Box>);
    }
}


/** Class to display server responses **/
class ChatServerMessage extends React.Component {
    render() {
        let type = this.props.data["_type"];
        let content = <Box></Box>
        if (type === "datasets") {
            content = <DatasetsMessage data={this.props.data["datasets"]} />
        }
        return (<Box className="chat-response">{content}</Box>)
    }
}


export default ChatServerMessage;