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
class ControllerSettingsBox extends React.Component {
    render() {
        let dataset_items = this.props.datasets.map((x, i) => {
            return (<MenuItem key={i} value={x["label"]}>{x["label"]}</MenuItem>);
        });
        return(<Grid container spacing={2}>
                <Grid item xs={8}>
                    <Typography variant="h5">Search space</Typography>
                    <Table><TableBody><TableRow >
                        <TableCell component="td" scope="row" className={"column-dataset"}>
                            Dataset
                        </TableCell>
                        <TableCell>
                            <TextField select id="controller-dataset"
                                       defaultValue={this.props.dataset}
                                       value={this.props.dataset}
                                       onChange={(e) => this.props.update("dataset", e.target.value)}
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
                                defaultValue={3}
                                getAriaValueText={intValueText}
                                aria-labelledby="discrete-slider"
                                valueLabelDisplay="auto"
                                marks step={1} min={1} max={20}
                                onChangeCommitted={(e, value) => this.props.update("n", value)}
                            />
                        </TableCell>
                    </TableRow>
                    </TableBody></Table>
                </Grid>
                <Grid item xs={8}>
                    <Typography variant="h5">Diffusion</Typography>
                    <Table>
                        <TableBody>
                            {this.props.datasets.map(row => (
                                <TableRow key={row.label}>
                                    <TableCell component="td" scope="row" className={"column-dataset"}>
                                        {row.label}
                                    </TableCell>
                                    <TableCell>
                                        <Slider
                                            defaultValue={0}
                                            getAriaValueText={floatValueText}
                                            aria-labelledby="discrete-slider"
                                            valueLabelDisplay="auto"
                                            step={0.01} min={0} max={10}
                                        />
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Grid>
                <Grid item xs={8}>
                    <Typography variant="h5">Indirect paths</Typography>
                    <Table><TableBody>
                            {this.props.datasets.map(row => (
                                <TableRow key={row.label}>
                                    <TableCell component="td" scope="row" className={"column-dataset"}>
                                        {row.label}
                                    </TableCell>
                                    <TableCell>
                                        <Slider
                                            defaultValue={0}
                                            getAriaValueText={intValueText}
                                            aria-labelledby="discrete-slider"
                                            valueLabelDisplay="auto"
                                            marks step={1} min={0} max={10}
                                        />
                                    </TableCell>
                                </TableRow>
                            ))}
                    </TableBody></Table>
                </Grid>
            </Grid>
        )
    }
}

export default ControllerSettingsBox;

