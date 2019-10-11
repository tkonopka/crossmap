import React from 'react';
import Typography from '@material-ui/core/Typography';
import TableBody from "@material-ui/core/TableBody";
import TableRow from "@material-ui/core/TableRow";
import TableCell from "@material-ui/core/TableCell";
import Table from "@material-ui/core/Table";



/** a chat message with information provided by a user **/
class ChatUserMessage extends React.Component {
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
            <div className="chat-user">
                <Table>
                    <TableBody>
                        {rows}
                    </TableBody>
                </Table>
            </div>
        )
    }
}


export default ChatUserMessage;