import React from 'react';
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
class ChatUserMessage extends ChatMessage {
    constructor(props) {
        super(props);
        this.toggleExtendedView = this.toggleExtendedView.bind(this);
        this.sendClone = this.sendClone.bind(this);
    }

    componentDidMount() {
        this.setState({extended: 0});
    }
    toggleExtendedView() {
        this.setState((prevState) => ({extended: (prevState.extended+1) %2 }));
    }
    sendClone() {
       this.props.clone(JSON.parse(JSON.stringify(this.props.data)));
    }

    render() {
        let data = this.props.data;
        let rows = ["data", "aux_pos", "aux_neg"].map((x) => {
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
                <Table>
                    <TableBody>
                        {rows}
                    </TableBody>
                </Table>
                <Box display={this.state.extended ? "block": "none"}>
                    hello
                </Box>
                <Box visibility={this.state.mouseover ? "visible": "hidden"}>
                    <Grid container direction="row" justify="flex-end" alignItems="flex-end">
                        <Button onClick={this.sendClone}>
                            <img src="icons/clone.svg"
                                 alt="clone settings"
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


export default ChatUserMessage;