import React from 'react';
import Grid from '@material-ui/core/Grid';
import Slider from '@material-ui/core/Slider';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';
import MenuItem from "@material-ui/core/MenuItem";
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableRow from '@material-ui/core/TableRow';


// helpers to format numbers into text for slider mouseover
function intValueText(value) {
    return `${parseInt(value)}`;
}
function floatValueText(value) {
    return `${value.toPrecision(4)}`;
}

/**
 * A Form with sliders allowing to set number of auxiliary documents, diffusion, etc.
 * Used to fine-tune a search or decomposition query
 */
class ControllerSettingsForm extends React.Component {
    render() {
        let settings = this.props.settings;
        //console.log("rendering settings form with settings: "+JSON.stringify(settings));
        let update = this.props.update;
        let dataset = settings.dataset;
        // contents of drop-down (selection of primary dataset)
        let dataset_items = this.props.datasets.map((x, i) => {
            return (<MenuItem key={i} value={x["label"]}>{x["label"]}</MenuItem>);
        });
        // sliders for diffusion
        let diffusion_sliders = this.props.datasets.map((row) => {
            return(<TableRow key={row.label}>
                <TableCell component="td" scope="row" className={"column-dataset"}>
                    {row.label}
                </TableCell>
                <TableCell>
                    <Slider
                        value={settings.diffusion[row.label]}
                        getAriaValueText={floatValueText}
                        aria-labelledby="discrete-slider"
                        valueLabelDisplay="auto"
                        onChange={(e, value) => update(row.label, value, "diffusion")}
                        step={0.01} min={0} max={10}
                    />
                </TableCell>
            </TableRow>)
        })
        // sliders for indirect paths
        let paths_sliders = this.props.datasets.map((row) => {
            if (row.label === dataset) { return null }
            return(<TableRow key={row.label}>
                <TableCell component="td" scope="row" className={"column-dataset"}>
                    {row.label}
                </TableCell>
                <TableCell>
                    <Slider
                        value={settings.paths[row.label]}
                        getAriaValueText={intValueText}
                        aria-labelledby="discrete-slider"
                        valueLabelDisplay="auto"
                        onChange={(e, value) => update(row.label, value, "paths")}
                        marks step={1} min={0} max={10}
                    />
                </TableCell>
            </TableRow>)
        }).filter((x) => ( x!== null));
        if (paths_sliders.length === 0) {
            paths_sliders.push(<TableRow key={0}><TableCell>No other datasets available</TableCell></TableRow>)
        }

        return(<Grid container spacing={2}>
                <Grid item xs={8}>
                    <Typography variant="h5">Search space</Typography>
                    <Table><TableBody><TableRow >
                        <TableCell component="td" scope="row" className={"column-dataset"}>
                            Dataset
                        </TableCell>
                        <TableCell>
                            <TextField select id="controller-dataset"
                                       value={settings.dataset}
                                       onChange={(e) => update("dataset", e.target.value)}
                                       fullWidth>
                                {dataset_items}
                            </TextField>
                        </TableCell>
                    </TableRow>
                    <TableRow>
                        <TableCell component="td" scope="row" className={"column-dataset"}>
                            Number of neighbors
                        </TableCell>
                        <TableCell>
                            <Slider
                                value={settings.n}
                                getAriaValueText={intValueText}
                                aria-labelledby="discrete-slider"
                                valueLabelDisplay="auto"
                                marks step={1} min={1} max={20}
                                onChangeCommitted={(e, value) => update("n", value)}
                            />
                        </TableCell>
                    </TableRow>
                    </TableBody></Table>
                </Grid>
                <Grid item xs={8}>
                    <Typography variant="h5">Diffusion</Typography>
                    <Table><TableBody>{diffusion_sliders}</TableBody></Table>
                </Grid>
                <Grid item xs={8}>
                    <Typography variant="h5">Indirect paths</Typography>
                    <Table><TableBody>{paths_sliders}</TableBody></Table>
                </Grid>
            </Grid>
        )
    }
}

export default ControllerSettingsForm;

