import React from 'react';
import AddIcon from '@material-ui/icons/Add';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Grid from '@material-ui/core/Grid';
import MenuItem from "@material-ui/core/MenuItem";


/** a chat message with a response provided by the server **/
class ControllerAddForm extends React.Component {
    constructor(props) {
        super(props);
        this.toggleMode = this.toggleMode.bind(this);
        this.state = { mode: "selecting" }
    }

    toggleMode() {
        console.log("toggling mode with current mode "+this.state.mode);
        this.setState((prevState) => ({
            "mode": (prevState.mode === "selecting") ? "typing" : "selecting"
        }));
    }

    render() {
        let dataset_items = this.props.datasets.map((x, i) => {
            return (<MenuItem key={i} value={x["label"]}>{x["label"]}</MenuItem>);
        });
        let settings = this.props.settings;
        let dataset_choice = null, dataset_toggle=null;
        if (this.state.mode === "selecting") {
            dataset_choice = <Grid item xs={6} lg={3}>
                                <TextField select fullWidth
                                           id="dataset" label="Dataset"
                                           value={settings.train_dataset}
                                           onChange={(e) => this.props.update("train_dataset", e.target.value)}>
                                    {dataset_items}
                                </TextField>
                             </Grid>;
            dataset_toggle = <Grid item xs={3}><Button variant="contained" onClick={this.toggleMode}>
                                <AddIcon/> New collection
                            </Button></Grid>;
        } else {
            dataset_choice = <Grid item xs={6} lg={3}>
                                <TextField fullWidth required id="dataset" label="Dataset"
                                           value={this.props.dataset}
                                           onChange={(e) => this.props.update("train_dataset", e.target.value)} />
                             </Grid>
            dataset_toggle = <Grid item xs={3}><Button variant="contained" onClick={this.toggleMode}>
                                Choose existing dataset
                             </Button></Grid>
        }

        return(<form autoComplete="off">
            <Grid container alignItems="center" justify="flex-start" spacing={2}>
                {dataset_choice}
                {dataset_toggle}
            </Grid>
            <Grid container alignItems="center" justify="flex-start" spacing={2}>
                <Grid item xs={6} lg={3}>
                    <TextField fullWidth
                               id="id"
                               onInput={(e) => this.props.update("id", e.target.value)}
                               label="Identifier" defaultValue=""/>
                </Grid>
                <Grid item xs={12}>
                    <TextField fullWidth
                               id="title"
                               onInput={(e) => this.props.update("title", e.target.value)}
                               label="Title" defaultValue=""/>
                </Grid>
                <Grid item xs={12}>
                    <TextField fullWidth multiline
                               id="data" rowsMax="12"
                               onInput={(e) => this.props.update("data", e.target.value)}
                               label="Data" defaultValue=""/>
                </Grid>
                <Grid item xs={12}>
                    <TextField fullWidth multiline
                               id="aux_pos" rowsMax="12"
                               onInput={(e) => this.props.update("aux_pos", e.target.value)}
                               label="Auxiliary data (positive weight)" defaultValue=""/>
                </Grid>
                <Grid item xs={12}>
                    <TextField fullWidth multiline
                               id="aux_neg" rowsMax="12"
                               onInput={(e) => this.props.update("aux_neg", e.target.value)}
                               label="Auxiliary data (negative weight)" defaultValue=""/>
                </Grid>
                <Grid item xs={12}>
                    <TextField fullWidth multiline
                               id="metadata" rowsMax="4"
                               onInput={(e) => this.props.update("metadata", e.target.value)}
                               label="Comment" defaultValue=""/>
                </Grid>
            </Grid>
        </form>)
    }
}

export default ControllerAddForm;
