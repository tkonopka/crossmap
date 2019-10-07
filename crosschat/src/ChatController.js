import React from 'react';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import MenuItem from '@material-ui/core/MenuItem';
import Fab from '@material-ui/core/Fab';
import Box from '@material-ui/core/Box';
import AddForm from './AddForm';
import ChatQueryBox from './ChatQueryBox'


/** a chat message with a response provided by the server **/
class ChatController extends React.Component {
    constructor(props) {
        super(props);
        this.handleChangeAction= this.handleChangeAction.bind(this);
        this.toggleSearchView = this.toggleSearchView.bind(this);
        this.state = {"action": "search", "view": "search", "extended": 0}
    }

    handleChangeAction = function(event) {
        this.setState({"action": event.target.value});
    };
    toggleSearchView = function() {
        this.setState((prevstate) => ({ extended: (prevstate.extended+1)%2}));
    };

    render() {
        let middlebox = [];
        if (this.state.view === "search") {
            middlebox.push(<ChatQueryBox key={0} extended={this.state.extended}/>)
        } else if (this.state.view === "add") {
            middlebox.push(<AddForm key={1} />)
        }

        return(<div id="crosschat-controller">
        <Grid container direction="row" justify="flex-start" alignItems="flex-start" spacing={2}>
            <Grid item xs={2}>
                <TextField select id="controller-action" variant="filled" label="Action"
                           value={this.state.action} onChange={this.handleChangeAction}
                           fullWidth margin="normal">
                    <MenuItem value="search">Search</MenuItem>
                    <MenuItem value="decompose">Decompose</MenuItem>
                    <MenuItem value="train">Train</MenuItem>
                </TextField>
                <Box m={1}>
                <Grid container direction="row" justify="space-around" alignItems="baseline">
                    <Button>
                        <img src="icons/ellipsis-v.svg" alt="toggle small/extended search view"
                             className="controller-icon"
                             onClick={this.toggleSearchView}
                        />
                    </Button>
                    <Button>
                        <img
                            src="icons/sliders-h.svg"
                            alt="Configuration"
                            className="controller-icon"
                        />
                    </Button>
                </Grid>
                </Box>
            </Grid>
            <Grid item xs={9}>
                {middlebox}
            </Grid>
            <Grid item xs={1} className="col-send" margin="normal"><Box m={1}>
                <Fab color="primary" aria-label="add">Send</Fab>
            </Box></Grid>
        </Grid>
        </div>);
    }
}

export default ChatController;
