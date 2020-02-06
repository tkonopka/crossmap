import React from 'react';
import Box from '@material-ui/core/Box';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import Collapse from '@material-ui/core/Collapse';
import ExpandLess from '@material-ui/icons/ExpandLess';
import ExpandMore from '@material-ui/icons/ExpandMore';
import Typography from '@material-ui/core/Typography';
import TableBody from "@material-ui/core/TableBody";
import TableRow from "@material-ui/core/TableRow";
import TableHead from '@material-ui/core/TableHead';
import TableCell from "@material-ui/core/TableCell";
import TablePagination from '@material-ui/core/TablePagination';
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
        props.setHeader(header + " result");
        this.state = {value_column: value_column, value_header: value_header};
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
                <Table size={"small"}>
                    <TableHead>{header}</TableHead>
                    <TableBody>{content}</TableBody>
                </Table>
                <Box visibility={this.state.mouseover ? "visible": "hidden"}>
                <Grid container direction="row" justify="flex-end" alignItems="flex-end">
                    <Button onClick={this.handleClipboard}>
                        <img src="icons/clipboard.svg" alt="copy results to clipboard"
                             className="chat-icon"/>
                    </Button>
                </Grid>
                </Box>
            </div>)
    }
}


/** Box showing a list of datasets **/
class DatasetsMessage extends ChatMessage {
    constructor(props) {
        super(props);
        props.setHeader("Available datasets");
        this.handleChangePage = this.handleChangePage.bind(this);
        this.handleChangeRowsPerPage = this.handleChangeRowsPerPage.bind(this);
        this.state = {page: 0, rowsPerPage: 10}
    }

    handleChangePage(event, newPage) {
        this.setState({page: newPage})
    };

    handleChangeRowsPerPage(event) {
        this.setState({page: 0, rowsPerPage: parseInt(event.target.value, 10)});
    };

    render() {
        let rows = this.props.data["datasets"];
        if (rows.length === 0) {
            return(<div className={"no-datasets"}><Typography>There are no datasets available</Typography></div>)
        }
        let header = <TableRow>
            <TableCell>Dataset</TableCell>
            <TableCell>Size</TableCell>
        </TableRow>;
        let page = this.state.page;
        let rowsPerPage = this.state.rowsPerPage;
        let content = rows.slice(page * rowsPerPage, (page * rowsPerPage) + rowsPerPage)
            .map(function (x, i) {
                return (<TableRow key={x["label"]}>
                    <TableCell><Typography color={"primary"}>{x["label"]}</Typography></TableCell>
                    <TableCell className="chat-td-numeric">
                        <Typography color={"secondary"}>{x["size"]}</Typography>
                    </TableCell>
                </TableRow>)
            });
        let pagination = null;
        if (rows.length>10) {
            pagination = <TablePagination
                rowsPerPageOptions={[5, 10, 25]}
                component="div"
                count={rows.length}
                rowsPerPage={this.state.rowsPerPage}
                page={this.state.page}
                onChangePage={this.handleChangePage}
                onChangeRowsPerPage={this.handleChangeRowsPerPage}
            />;
        }
        return (
            <div onMouseEnter={this.handleMouseEnter} onMouseLeave={this.handleMouseLeave}>
                <Table size={"small"}>
                    <TableHead>{header}</TableHead>
                    <TableBody>{content}</TableBody>
                </Table>
                {pagination}
            </div>)
    }
}


/** Box success/failure adding a new item into db**/
class AddMessage extends ChatMessage {
    constructor(props) {
        super(props);
        props.setHeader("Add");
    }
    render() {
        let dataset = this.props.data["dataset"];
        let idx = parseInt(this.props.data["idx"]);
        let content = "";
        if (idx>0) {
            content = <p>Added new item into dataset: {dataset}</p>
        } else if (idx === 0) {
            content = <p>Created new dataset with one item: {dataset}</p>
        } else {
            content = <p>Something went wrong.</p>
        }
        return(<div xs={8}>{content}</div>);
    }
}


/** Box showing features and values in a table with pagination **/
class DiffusionMessage extends ChatMessage {
    constructor(props) {
        super(props);
        props.setHeader("Diffusion result");
        this.handleChangePage = this.handleChangePage.bind(this);
        this.handleChangeRowsPerPage = this.handleChangeRowsPerPage.bind(this);
        this.state = {page: 0, rowsPerPage: 10}
    }

    handleChangePage(event, newPage) {
        this.setState({page: newPage})
    };

    handleChangeRowsPerPage(event) {
        this.setState({page: 0, rowsPerPage: parseInt(event.target.value, 10)});
    };

    render() {
        let rows = this.props.data["features"];
        let header = <TableRow>
            <TableCell>Feature</TableCell>
            <TableCell>Value</TableCell>
        </TableRow>;
        let page = this.state.page;
        let rowsPerPage = this.state.rowsPerPage;
        let content = rows.slice(page * rowsPerPage, (page * rowsPerPage) + rowsPerPage)
            .map(function(x, i) {
            return (<TableRow key={x["feature"]}>
                <TableCell><Typography color={"secondary"}>{x["feature"]}</Typography></TableCell>
                <TableCell className="chat-td-numeric">
                    <Typography color={"secondary"}>{x["value"].toPrecision(4)}</Typography>
                </TableCell>
            </TableRow>)
        });
        return (
            <div onMouseEnter={this.handleMouseEnter} onMouseLeave={this.handleMouseLeave}>
                <Table size={"small"}>
                    <TableHead>{header}</TableHead>
                    <TableBody>{content}</TableBody>
                </Table>
                <TablePagination
                    rowsPerPageOptions={[5, 10, 25]}
                    component="div"
                    count={rows.length}
                    rowsPerPage={this.state.rowsPerPage}
                    page={this.state.page}
                    onChangePage={this.handleChangePage}
                    onChangeRowsPerPage={this.handleChangeRowsPerPage}
                />
            </div>)
    }
}


/** Class to display server responses **/
class ChatServerMessage extends React.Component {
    constructor(props) {
        super(props);
        this.toggleOpen = this.toggleOpen.bind(this);
        this.setHeader = this.setHeader.bind(this);
        this.state = {open: true, header: ""};
    }

    toggleOpen = function() {
        this.setState((prevstate) => ({ open: !prevstate.open}));
    };
    setHeader = function(x) {
        this.setState({header: x})
    }

    render() {
        let type = this.props.data["_type"];
        let content = <div></div>
        if (type === "datasets") {
            content = <DatasetsMessage data={this.props.data} setHeader={this.setHeader}/>
        } else if (type === "search" || type === "decompose") {
            content = <HitsMessage data={this.props.data} setHeader={this.setHeader}/>
        } else if (type === "diffuse") {
            content = <DiffusionMessage data={this.props.data} setHeader={this.setHeader}/>
        } else if (type==="add") {
            content = <AddMessage data={this.props.data} setHeader={this.setHeader}/>
        }
        return(<div className="chat-response">
            <List component="nav">
                <ListItem button onClick={this.toggleOpen} className="chat-response-toggle">
                    <ListItemText className="chat-response-header">{this.state.header}</ListItemText>
                    { this.state.open ? <ExpandLess/> : <ExpandMore/>}
                </ListItem>
                <Collapse in={this.state.open} timeout="auto" unmountOnExit>
                    {content}
                </Collapse>
            </List>
            </div>
        )
    }
}


export default ChatServerMessage;

