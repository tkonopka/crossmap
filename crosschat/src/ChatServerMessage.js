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


/** a chat message with a response provided by the server **/
class HitsMessage extends React.Component {
    constructor(props) {
        super(props);
        this.handleMouseEnter = this.handleMouseEnter.bind(this);
        this.handleMouseLeave = this.handleMouseLeave.bind(this);
        this.handleClipboard = this.handleClipboard.bind(this);
        this.state = {mouseover: 0}
    }

    handleMouseEnter() {
        this.setState({mouseover: 1})
    }
    handleMouseLeave() {
        this.setState({mouseover: 0})
    }
    handleClipboard() {
        console.log("clipboard");
    }

    render() {
        let type = this.props.data["_type"];
        let targets = this.props.data["targets"];
        let titles = this.props.data["titles"];
        let hits_header = "Search", value_column = "Distance", values = null;
        if (type === "search") {
            values = this.props.data["distances"];
        } else if (type === "decompose") {
            console.log("using decomposition");
            hits_header = "Decomposition";
            value_column = "Weight";
            values = this.props.data["coefficients"];
        }
        let header = <TableRow>
            <TableCell>id</TableCell>
            <TableCell>Title</TableCell>
            <TableCell>{value_column}</TableCell>
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
                <Typography variant={"h4"}>{hits_header}</Typography>
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


class DatasetsMessage extends React.Component {
    render() {
        //console.log(JSON.stringify(this.props.data));
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