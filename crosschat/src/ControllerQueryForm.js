import React from 'react';
import Grid from '@material-ui/core/Grid';
import TextField from '@material-ui/core/TextField';
import Box from '@material-ui/core/Box';


/**
 * A Form with several textboxes.
 * Used to compose a user query with primary data and auxiliary fields.
 */
class ControllerQueryForm extends React.Component {
    render() {
        let neg_visibility = "hidden";
        if (this.props.extended) {
            neg_visibility = "visible"
        }
        console.log("Rendering extended state: "+this.props.extended + " visibility: "+neg_visibility);
        return(<form autoComplete="off">
            <Grid container spacing={1}>
                <Grid item xs={12}>
                    <TextField id="query-data" fullWidth multiline rowsMax={8}
                               onInput={(e) => this.props.update("data", e.target.value)}
                               label="Query" defaultValue="" margin="normal"/>
                    <Box visibility={neg_visibility}>
                        <TextField id="query-aux-neg" fullWidth multiline rowsMax={8}
                                   onInput={(e) => this.props.update("aux_neg", e.target.value)}
                                   label="Auxiliary data (negative weight)" defaultValue="" margin="normal"
                        />
                    </Box>
                </Grid>
            </Grid>
            </form>
        )
    }
}

export default ControllerQueryForm;
