import React from 'react';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import MenuItem from '@material-ui/core/MenuItem';
import Fab from '@material-ui/core/Fab';
import Box from '@material-ui/core/Box';
import ControllerAddForm from './ControllerAddForm';
import ControllerQueryForm from './ControllerQueryForm';
import ControllerSettingsBox from './ControllerSettingsBox';


/** a chat message with a response provided by the server **/
class Controller extends React.Component {
    constructor(props) {
        super(props);
        console.log("Controller constructor with props "+JSON.stringify(props));
        this.handleChangeAction = this.handleChangeAction.bind(this);
        this.toggleSearchView = this.toggleSearchView.bind(this);
        this.showSettingsView = this.showSettingsView.bind(this);
        this.handlePayloadUpdate = this.handlePayloadUpdate.bind(this);
        this.composeAndSend = this.composeAndSend.bind(this);
        let dataset = "";
        if (props.datasets.length > 0) {
            dataset = props.datasets[0]["label"];
        }
        console.log("setting state with "+dataset);
        this.state = {"action": "search", "view": "search", "extended": 0,
                      "dataset": dataset,
                       "n": 1, "data": "", "aux_neg": ""}
    }

    handleChangeAction = function(event) {
        this.setState({"action": event.target.value});
    };
    toggleSearchView = function() {
        this.setState((prevstate) => ({ extended: (prevstate.extended+1)%2, view: "search" }));
    };
    showSettingsView = function() {
        this.setState({ view: "settings"});
    };
    handlePayloadUpdate = function(key, value) {
        console.log("payload update: "+key+": "+value);
        let obj = {};
        obj[key] = value;
        this.setState(obj);
    };
    composeAndSend = function() {
        let dataset = this.state.dataset;
        if (dataset === "") {
            if (this.props.datasets.length>0) {
                dataset = this.props.datasets[0]["label"];
                this.setState({dataset: dataset})
            } else {
                return
            }
        }
        const action = this.state.action;
        let result = {}
        if (action === "search" || action === "decompose") {
            result = { "n": this.state.n,
                       "data": this.state.data,
                       "aux_neg": this.state.aux_neg
            }
        }
        result["dataset"] = dataset;
        console.log("composed: "+JSON.stringify(result));
        this.props.send(result, action)
    };

    render() {
        let middlebox = [];
        const view = this.state.view
        if (view === "search") {
            middlebox.push(<ControllerQueryForm key={0}
                                                extended={this.state.extended}
                                                update={this.handlePayloadUpdate}/>)
        } else if (view === "add") {
            middlebox.push(<ControllerAddForm key={1} />)
        } else if (view === "settings") {
            middlebox.push(<ControllerSettingsBox key={2}
                                                  datasets={this.props.datasets}
                                                  dataset={this.state.dataset}
                                                  update={this.handlePayloadUpdate}/>)
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
                            onClick={this.showSettingsView}
                        />
                    </Button>
                </Grid>
                </Box>
            </Grid>
            <Grid item xs={9}>
                {middlebox}
            </Grid>
            <Grid item xs={1} className="col-send" margin="normal"><Box m={1}>
                <Fab color="primary" aria-label="add" onClick={this.composeAndSend}>Send</Fab>
            </Box></Grid>
        </Grid>
        </div>);
    }
}

export default Controller;
