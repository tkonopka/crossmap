import React from 'react';
import Grid from '@material-ui/core/Grid';
import Slider from '@material-ui/core/Slider';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';
import Box from '@material-ui/core/Box';


// helpers to format numbers into text for slider mouseover
function intValuetext(value) {
    return `${parseInt(value)}`;
}
function floatValueText(value) {
    return `${value.toPrecision(4)}`;
}

/**
 * A Form with sliders allowing to set number of auxiliary documents, diffusion, etc.
 * Used to fine-tune a search or decomposition query
 */
class SettingsBox extends React.Component {
    constructor(props) {
        super(props);
        this.state = {data: "", aux_neg: ""}
    }

    render() {
        console.log("Rendering settings: " + JSON.stringify(this.props.datasets));
        return(<form autoComplete="off">
            <Grid container spacing={1}>
                <Grid item xs={7}>
                    <Typography variant="p" gutterBottom>
                        Number of neighbors
                    </Typography>
                    <Slider
                        defaultValue={3}
                        getAriaValueText={intValuetext}
                        aria-labelledby="discrete-slider"
                        valueLabelDisplay="auto"
                        marks step={1} min={1} max={20}
                    />
                </Grid>
                <Grid item xs={7} >
                    <Typography variant="p" gutterBottom>
                        Diffusion
                    </Typography>
                    <Grid>
                        <Slider
                            defaultValue={3}
                            getAriaValueText={intValuetext}
                            aria-labelledby="discrete-slider"
                            valueLabelDisplay="auto"
                            marks step={1} min={1} max={20}
                        />
                    </Grid>
                </Grid>
                <Grid item xs={7} >
                    <Typography variant="p" gutterBottom>
                        Indirect paths
                    </Typography>
                    <Grid>
                        <Slider
                            defaultValue={0}
                            getAriaValueText={intValuetext}
                            aria-labelledby="discrete-slider"
                            valueLabelDisplay="auto"
                            marks step={1} min={0} max={10}
                        />
                    </Grid>
                </Grid>
            </Grid>
            </form>
        )
    }
}

export default SettingsBox;
