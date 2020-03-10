import React from 'react';
import Slider from "@material-ui/core/Slider";
import Typography from '@material-ui/core/Typography';
import TableBody from "@material-ui/core/TableBody";
import TableRow from "@material-ui/core/TableRow";
import TableCell from "@material-ui/core/TableCell";
import Table from "@material-ui/core/Table";
import ChatMessage from "./ChatMessage"
import Grid from "@material-ui/core/Grid";
import Button from "@material-ui/core/Button";
import Box from "@material-ui/core/Box";


/** a chat message with information provided by a user **/
class UserQueryMessage extends ChatMessage {
    constructor(props) {
        super(props);
        this.toggleExtendedView = this.toggleExtendedView.bind(this);
        this.sendClone = this.sendClone.bind(this);
        this.sendDeepClone = this.sendDeepClone.bind(this);
    }

    componentDidMount() {
        this.setState({extended: 0});
    }
    toggleExtendedView() {
        this.setState((prevState) => ({extended: (prevState.extended+1) %2 }));
    }
    /** shallow clone - copy only the text inputs **/
    sendClone() {
        let shallow_copy = {"data_pos": this.props.data["data_pos"],
                            "data_neg": this.props.data["data_neg"]};
       this.props.clone(JSON.parse(JSON.stringify(shallow_copy)));
    }
    /** deeper clone - copies both text inputs and query settings **/
    sendDeepClone() {
        this.props.clone(JSON.parse(JSON.stringify(this.props.data)));
    }

    render() {
        let data = this.props.data;
        // console.log("rendering user message with data: "+JSON.stringify(data));
        let rows = ["data_pos", "data_neg"].map((x) => {
            if (data[x]===undefined) {
                return null;
            }
            if (data[x] !== "") {
                return(<TableRow key={x}>
                    <TableCell><Typography>{data[x]}</Typography></TableCell>
                    <TableCell className="chat-td-label"><Typography color="secondary">{x}</Typography></TableCell>
                </TableRow>)
            }
            return null;
        });
        let settings_datasets = Object.keys(data.diffusion);
        let diffusion_marks = [0, 0.5, 1, 1.5, 2].map((x) => ({value: x, label: x}));
        let diffusion_rows = settings_datasets.map((d) => {
            return(<TableRow key={"diffusion_"+d}>
                <TableCell variant="head">{d===settings_datasets[0] ? "diffusion" : ""}</TableCell>
                <TableCell>{d}</TableCell>
                <TableCell><Slider disabled
                                   value={data["diffusion"][d]}
                                   valueLabelDisplay="auto"
                                   marks={diffusion_marks}
                                   min={0} max={2}/>
                </TableCell>
            </TableRow>)
        });
        return (
            <div className="chat-user" onMouseEnter={this.handleMouseEnter} onMouseLeave={this.handleMouseLeave}>
                <Typography variant={"h5"}>Query</Typography>
                <Table>
                    <TableBody>
                        {rows}
                    </TableBody>
                </Table>
                <Box display={this.state.extended ? "block": "none"} className={"chat-user-settings"}>
                    <Typography variant={"h5"}>Settings</Typography>
                    <Table size={"small"}>
                        <colgroup>
                            <col style={{width: '35%'}}/>
                            <col style={{width: '30%'}}/>
                            <col style={{width: '30%'}}/>
                        </colgroup>
                        <TableBody>
                            <TableRow>
                                <TableCell variant={"head"}>action</TableCell>
                                <TableCell>{data["action"]}</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell variant={"head"}>dataset</TableCell>
                                <TableCell>{data["dataset"]}</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell variant={"head"}>number of neighbors</TableCell>
                                <TableCell>{data["n"]}</TableCell>
                            </TableRow>
                            {diffusion_rows}
                         </TableBody>
                    </Table>
                </Box>
                <Box visibility={this.state.mouseover ? "visible": "hidden"}>
                    <Grid container direction="row" justify="flex-end" alignItems="flex-end">
                        <Button onClick={this.sendClone}>
                            <img src="icons/clone.svg"
                                 alt="clone - text only"
                                 className="chat-icon"/>
                        </Button>
                        <Button onClick={this.sendDeepClone}>
                            <img src="icons/deepclone.svg"
                                 alt="deep clone - text and settings"
                                 className="chat-icon"/>
                        </Button>
                        <Button onClick={this.toggleExtendedView}>
                            <img src="icons/cog.svg"
                                 alt="toggle display of query details"
                                 className="chat-icon"/>
                        </Button>
                    </Grid>
                </Box>
            </div>
        )
    }
}


class UserAddMessage extends ChatMessage {
    constructor(props) {
        super(props);
        this.toggleExtendedView = this.toggleExtendedView.bind(this);
    }

    componentDidMount() {
        this.setState({extended: 0});
    }
    toggleExtendedView() {
        this.setState((prevState) => ({extended: (prevState.extended+1) %2 }));
    }

    render() {
        let data = this.props.data;
        let rows = ["title", "data_pos", "data_neg"].map((x) => {
            if (data[x]===undefined) {
                return null;
            }
            if (data[x] !== "") {
                return(<TableRow key={x}>
                    <TableCell><Typography>{data[x]}</Typography></TableCell>
                    <TableCell className="chat-td-label"><Typography color="secondary">{x}</Typography></TableCell>
                </TableRow>)
            }
            return null;
        });
        return (
            <div className="chat-user" onMouseEnter={this.handleMouseEnter} onMouseLeave={this.handleMouseLeave}>
                <Typography variant={"h5"}>Add</Typography>
                <Table>
                    <TableBody>
                        {rows}
                    </TableBody>
                </Table>
            </div>
        )
    }
}


/** Class to display server responses **/
class ChatUserMessage extends React.Component {
    render() {
        let action = this.props.data["action"];
        if (["search", "decompose", "diffuse"].includes(action)) {
            return (<UserQueryMessage data={this.props.data} clone={this.props.clone} />);
        } else if (action === "add") {
            return (<UserAddMessage data={this.props.data} />);
        }
    }
}


export default ChatUserMessage;

