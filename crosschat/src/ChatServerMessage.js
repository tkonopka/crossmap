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
import Button from "@material-ui/core/Button";
import Grid from "@material-ui/core/Grid";
import ChatMessage from "./ChatMessage";


/** a chat message with a response provided by the server **/
class HitsMessage extends ChatMessage {
    constructor(props) {
        super(props);
        this.handleClipboard = this.handleClipboard.bind(this);
        let type = props.data["_type"];
        let header="Search", value_column = "distances", value_header = "Distance";
        if (type === "decompose") {
            header = "Decomposition";
            value_column = "coefficients";
            value_header = "Coefficient";
        }
        this.state = {header: header, value_column: value_column, value_header: value_header};
    }

    handleClipboard() {
        let header_line = "ID\tTitle\t"+this.state.value_header;
        let titles = this.props.data["titles"];
        let values = this.props.data[this.state.value_column];
        let ids = this.props.data["targets"];
        let result = [header_line].concat(values.map(function(x,i) {
            return(ids[i]+"\t"+titles[i]+"\t"+x.toPrecision(4))
        }));
        if (navigator.clipboard) {
            navigator.clipboard.writeText(result.join("\n"))
        } else {
            alert("not supported?")
        }
    }

    render() {
        let targets = this.props.data["targets"];
        let titles = this.props.data["titles"];
        let values = this.props.data[this.state.value_column];
        let header = <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>Title</TableCell>
            <TableCell>{this.state.value_header}</TableCell>
        </TableRow>;
        let content = values.map(function(x, i) {
            return (<TableRow key={i}>
                <TableCell><Typography color={"secondary"}>{targets[i]}</Typography></TableCell>
                <TableCell><Typography color={"primary"}>{titles[i]}</Typography></TableCell>
                <TableCell className="chat-td-numeric"><Typography color={"secondary"}>{x.toPrecision(4)}</Typography></TableCell>
            </TableRow>)
        });
        return (
            <div onMouseEnter={this.handleMouseEnter} onMouseLeave={this.handleMouseLeave}>
                <Typography variant={"h4"}>{this.state.header}</Typography>
                <Table>
                    <TableHead>{header}</TableHead>
                    <TableBody>{content}</TableBody>
                </Table>
                <Box visibility={this.state.mouseover ? "visible": "hidden"}>
                <Grid container direction="row" justify="flex-end" alignItems="flex-end">
                    <Button onClick={this.handleClipboard}>
                        <img src="icons/clipboard.svg" alt="toggle small/extended search view"
                             className="chat-icon"/>
                    </Button>
                </Grid>
                </Box>
            </div>)
    }
}


class DatasetsMessage extends ChatMessage {
    render() {
        let datasets = this.props.data["datasets"].map((x, i) => {
            return(
                <ListItem key={i}>
                <ListItemText primary={x["label"]} secondary={x["size"] + " items"}/>
                </ListItem>
            )
        });
        return(<div xs={8}>
            <Typography variant="h6">Available Datasets</Typography>
            <List>{datasets}</List>
        </div>);
    }
}


/** Class to display server responses **/
class ChatServerMessage extends React.Component {
    render() {
        let type = this.props.data["_type"];
        let content = <div></div>
        if (type === "datasets") {
            content = <DatasetsMessage data={this.props.data} />
        } else if (type === "search" || type === "decompose") {
            content = <HitsMessage data={this.props.data} />
        }
        return (<div className="chat-response">{content}</div>)
    }
}


export default ChatServerMessage;