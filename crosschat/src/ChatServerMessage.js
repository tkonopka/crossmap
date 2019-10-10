import React from 'react';
import Box from '@material-ui/core/Box';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import Typography from '@material-ui/core/Typography';
import TableBody from "@material-ui/core/TableBody";
import TableRow from "@material-ui/core/TableRow";
import TableHead from '@material-ui/core/TableHead';
import TableCell from "@material-ui/core/TableCell";
import Table from "@material-ui/core/Table";


/** a chat message with a response provided by the server **/
class HitsMessage extends React.Component {
    render() {
        let type = this.props.data["_type"];
        let targets = this.props.data["targets"];
        let titles = this.props.data["titles"];
        let header = null, content = null;
        if (type === "search") {
            header = <TableRow>
                <TableCell>id</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Distance</TableCell>
            </TableRow>;
            content = this.props.data["distances"].map(function(x, i) {
                return (<TableRow key={i}>
                    <TableCell>{targets[i]}</TableCell>
                    <TableCell>{titles[i]}</TableCell>
                    <TableCell className="chat-td-numeric">{x}</TableCell>
                </TableRow>)
            });
        } else {
            header = <TableRow>
                <TableCell>id</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Weight</TableCell>
            </TableRow>;
            content = this.props.data["coefficients"].map(function(x, i) {
                return (<TableRow key={i}>
                    <TableCell>{targets[i]}</TableCell>
                    <TableCell>{titles[i]}</TableCell>
                    <TableCell className="chat-td-numeric">{x}</TableCell>
                </TableRow>)
            });
        }
        return (<Box className="chat-response"><Table>
                    <TableHead><TableHead/>{header}</TableHead>
                    <TableBody>{content}</TableBody>
                </Table></Box>)
    }
}


class DatasetsMessage extends React.Component {
    render() {
        console.log(JSON.stringify(this.props.data));
        let datasets = this.props.data["datasets"].map((x, i) => {
            return(
                <ListItem key={i}>
                <ListItemText primary={x["label"]} secondary={x["size"] + " items"}/>
                </ListItem>
            )
        });
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
        console.log("Server message of type " + type);
        console.log("data: "+JSON.stringify(this.props.data))
        let content = <Box></Box>
        if (type === "datasets") {
            content = <DatasetsMessage data={this.props.data} />
        } else if (type === "search" || type === "decomposition") {
            content = <HitsMessage data={this.props.data} />
        }
        return (<Box className="chat-response">{content}</Box>)
    }
}


export default ChatServerMessage;