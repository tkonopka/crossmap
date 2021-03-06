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
        this.showSearchView = this.showSearchView.bind(this);
        this.showSettingsView = this.showSettingsView.bind(this);
        this.handleStateUpdate = this.handleStateUpdate.bind(this);
        this.cloneFromQuery = this.cloneFromQuery.bind(this);
        this.composeAndSend = this.composeAndSend.bind(this);
        let dataset = "", train_dataset = "";
        let diffusion = {};
        if (props.datasets.length > 0) {
            dataset = props.datasets[0]["label"];
            train_dataset = props.datasets[props.datasets.length-1]["label"];
            props.datasets.map((x) => {
                diffusion[x["label"]] = 0;
                return null;
            })
        }
        this.state = {
            action: "search",
            view: "search",
            dataset: dataset,
            n: 1,
            data_pos: "",
            data_neg: "",
            id: "",
            title: "",
            metadata: "",
            diffusion: diffusion,
            train_dataset: train_dataset
        }
    }

    /** Transfer state from an object into the current state **/
    cloneFromQuery = function(query) {
        this.setState(query)
    };
    handleChangeAction = function(event) {
        let action = event.target.value;
        let view = (action === "add") ? "add" : "search";
        this.setState({"action": action, "view": view});
    };
    showSearchView = function() {
        this.setState({ view: "search" });
    };
    showSettingsView = function() {
        this.setState({ view: "settings"});
    };
    handleStateUpdate = function(key, value, group) {
        this.setState((prevstate) => {
            if (group === undefined) {
                return {[key]: value};
            }
            let obj = prevstate[group];
            obj[key] = value;
            return {[group]: obj};
        })
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
        if (!hasPayload(this.state)) {
            return null;
        }
        if (["search", "decompose", "diffuse"].includes(action)) {
            result = makeQueryPayload(this.state, this.props.datasets);
        } else if (action === "add") {
            result = makeTrainPayload(this.state)
        } else {
            return null;
        }
        this.props.send(result, action);
        this.setState({"data_pos": "", "data_neg": "",
                       "id": "", "title": "", "metadata": ""})
    };

    componentDidUpdate() {
        this.props.onresize(this.controllerElement.clientHeight)
    }

    render() {
        let middle = [];
        const view = this.state.view;
        if (view === "search") {
            middle.push(<ControllerQueryForm key={0}
                                                data_pos={this.state.data_pos}
                                                data_neg={this.state.data_neg}
                                                extended={this.state.extended}
                                                update={this.handleStateUpdate}
                                                send={this.composeAndSend}/>)
        } else if (view === "add") {
            middle.push(<ControllerAddForm key={1}
                                              settings={this.state}
                                              datasets={this.props.datasets}
                                              update={this.handleStateUpdate}/>)
        } else if (view === "settings") {
            middle.push(<ControllerSettingsForm key={2}
                                                   datasets={this.props.datasets}
                                                   settings={this.state}
                                                   update={this.handleStateUpdate}/>)
        }
        return(<div width={1} id="chat-controller"
                    ref={(divElement) => this.controllerElement = divElement}>
            <Grid container direction="row" justify="flex-start" alignItems="flex-start" spacing={2}>
                <Grid item xs={2}>
                    <TextField select id="controller-action" variant="filled" label="Action"
                               value={this.state.action} onChange={this.handleChangeAction}
                               fullWidth margin="normal">
                        <MenuItem value="search">Search</MenuItem>
                        <MenuItem value="decompose">Decompose</MenuItem>
                        <MenuItem value="diffuse">Diffuse</MenuItem>
                        <MenuItem value="add">Train</MenuItem>
                    </TextField>
                    <Box m={1}>
                    <Grid container direction="row" justify="space-around" alignItems="baseline">
                        <Box display={view === "add" ? "none" : "block"}>
                        <Button>
                            <img src="icons/search.svg" alt="toggle small/extended search view"
                                 className="controller-icon"
                                 onClick={this.showSearchView}/>
                        </Button>
                        <Button>
                            <img src="icons/sliders-h.svg"
                                 alt="Configuration"
                                 className="controller-icon"
                                 onClick={this.showSettingsView}/>
                        </Button></Box>
                    </Grid>
                    </Box>
                </Grid>
                <Grid item xs={9}>{middle}</Grid>
                <Grid item xs={1} className="col-send" margin="normal">
                    <Box m={1}>
                        <Fab color="primary" aria-label="add" onClick={this.composeAndSend}>Send</Fab>
                    </Box>
                </Grid>
            </Grid></div>);
    }
}

/**
 * A brute-force copy of an object via stringify and parse
 *
 * @param x object
 * @returns a copy of the input object
 */
let JSONcopy = function(x) {
    return JSON.parse(JSON.stringify(x));
};


/** Helper determines if query boxes have some nonempty values **/
let hasPayload = function(state) {
    return (state["data_pos"].trim() !== "");
};

/**
 * Helper to prepare a payload for search/ or decompose/
 */
let makeQueryPayload = function(state, datasets) {
    let dataset = state.dataset;
    if (dataset === "" && datasets.length>0) {
        dataset = datasets[0].label
    }
    if (dataset === "") return null;
    if (state.data_pos === "" && state.data_neg === "") return null;
    let result = {};
    let fields = ["action", "dataset", "n",
                  "data_pos", "data_neg", "diffusion"];
    fields.forEach((x)=> { result[x] = JSONcopy(state[x])});
    return result
};

/**
 * Helper to prepare a payload for train/
 */
let makeTrainPayload = function(state) {
    let result = { action: "add", dataset: state.train_dataset};
    ["id", "title", "data_pos", "data_neg", "metadata"].forEach((x) => {
        if (state[x] !== undefined) {
            result[x] = JSONcopy(state[x])
        } else {
            result[x] = "";
        }
    });
    return result
};


export default Controller;
