import React from 'react';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import MenuItem from '@material-ui/core/MenuItem';
import Fab from '@material-ui/core/Fab';
import Box from '@material-ui/core/Box';
import ControllerAddForm from './ControllerAddForm';
import ControllerQueryForm from './ControllerQueryForm';
import ControllerSettingsForm from './ControllerSettingsForm';


/** a chat message with a response provided by the server **/
class Controller extends React.Component {
    constructor(props) {
        super(props);
        this.handleChangeAction = this.handleChangeAction.bind(this);
        this.toggleSearchView = this.toggleSearchView.bind(this);
        this.showState = this.showState.bind(this);
        this.showSettingsView = this.showSettingsView.bind(this);
        this.handleStateUpdate = this.handleStateUpdate.bind(this);
        this.composeAndSend = this.composeAndSend.bind(this);
        let dataset = "";
        if (props.datasets.length > 0) {
            dataset = props.datasets[0]["label"];
        }
        this.state = {action: "search", view: "search", extended: 0,
                      dataset: dataset, n: 1, data: "", aux_neg: ""}
    }

    handleChangeAction = function(event) {
        let action = event.target.value;
        let view = (action === "add") ? "add" : "search";
        this.setState({"action": action, "view": view});
    };
    toggleSearchView = function() {
        this.setState((prevstate) => ({ extended: (prevstate.extended+1)%2, view: "search" }));
    };
    showSettingsView = function() {
        this.setState({ view: "settings"});
    };
    handleStateUpdate = function(key, value) {
        let obj = {};
        obj[key] = value;
        this.setState(obj);
    };
    showState = function() {
        console.log("state: "+JSON.stringify(this.state));
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
        let result = null;
        if (action === "search" || action === "decompose") {
          result = makePayload(this.state, this.props.datasets);
        }
        if (result === null) {
            return
        }
        console.log("composed: "+JSON.stringify(result));
        this.props.send(result, action)
    };

    componentDidUpdate() {
        this.props.onresize(this.controllerElement.clientHeight)
    }

    render() {
        let middlebox = [];
        const view = this.state.view;
        console.log("rendering controller with view: "+view);
        if (view === "search") {
            middlebox.push(<ControllerQueryForm key={0}
                                                data={this.state.data}
                                                aux_neg={this.state.aux_neg}
                                                extended={this.state.extended}
                                                update={this.handleStateUpdate}
                                                send={this.composeAndSend}/>)
        } else if (view === "add") {
            middlebox.push(<ControllerAddForm key={1}
                                              dataset={this.state.dataset}
                                              datasets={this.props.datasets}
                                              update={this.handleStateUpdate}/>)
        } else if (view === "settings") {
            middlebox.push(<ControllerSettingsForm key={2}
                                                   dataset={this.state.dataset}
                                                   datasets={this.props.datasets}
                                                   update={this.handleStateUpdate}/>)
        }

        return(<div width={1} id="chat-controller" ref={(divElement) => this.controllerElement = divElement}>
            <Grid container direction="row" justify="flex-start" alignItems="flex-start" spacing={2}>
            <Grid item xs={2}>
                <TextField select id="controller-action" variant="filled" label="Action"
                           value={this.state.action} onChange={this.handleChangeAction}
                           fullWidth margin="normal">
                    <MenuItem value="search">Search</MenuItem>
                    <MenuItem value="decompose">Decompose</MenuItem>
                    <MenuItem value="add">Train</MenuItem>
                </TextField>
                <Box m={1}>
                <Grid container direction="row" justify="space-around" alignItems="baseline">
                    <Button>
                        <img src="icons/search.svg" alt="toggle small/extended search view"
                             className="controller-icon"
                             onClick={this.toggleSearchView}
                        />
                    </Button>
                    <Button>
                        <img src="icons/sliders-h.svg"
                             alt="Configuration"
                             className="controller-icon"
                             onClick={this.showSettingsView}
                        />
                    </Button>
                    <Button>
                        <img src="icons/robot.svg"
                             alt="showState"
                             className="controller-icon"
                             onClick={this.showState}
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
            </Grid></div>);
    }
}

/**
 * Helper to prepare a payload from a controller state
 */
let makePayload = function(state, datasets) {
    let dataset = state.dataset;
    if (dataset === "" && datasets.length>0) {
        dataset = datasets[0].label
    }
    if (dataset === "" || (state.data === "" && state.aux_neg === "")) {
        return null;
    }
    let result = {
        "dataset": dataset,
        "n": state.n,
        "data": state.data,
        "aux_neg": state.aux_neg,
        "diffusion": {},
        "paths": {}
    };
    datasets.map(function(x) {
        let xlab = x.label;
        let val_diffusion = state["_diffusion_"+xlab];
        console.log("diffusion value for "+xlab + " "+val_diffusion);
        let val_paths = state["_paths_"+xlab];
        if (val_diffusion !== undefined) {
            result["diffusion"][xlab] = val_diffusion
        }
        if (val_paths !== undefined) {
            result["paths"][xlab] = val_paths
        }
        return null;
    });
    return result
}


export default Controller;
