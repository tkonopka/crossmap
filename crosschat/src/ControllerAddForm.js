import React from 'react';
import TextField from '@material-ui/core/TextField';
import Grid from '@material-ui/core/Grid';


/** a chat message with a response provided by the server **/
class ControllerAddForm extends React.Component {
    constructor(props) {
        super(props);
        this.state = {data: "", aux_pos: "", aux_neg: "", title: "", metadata: {}}
    }

    render() {
        return(<form autoComplete="off">
            <Grid container spacing={1}>
                <Grid item xs={12}>
            <TextField
                required
                id="id" fullWidth
                label="Identifier"
                defaultValue=""
                margin="normal"
            />
            <TextField
                id="title" fullWidth
                label="Title" defaultValue=""
                margin="normal"
            />
            <TextField
                id="data" fullWidth multiline rowsMax="12"
                label="Data" defaultValue=""
                margin="normal"
            />
            <TextField
                id="aux_pos" fullWidth multiline rowsMax="12"
                label="Auxiliary data (positive weight)" defaultValue=""
                margin="normal"
            />
            <TextField
                id="aux_neg" fullWidth multiline rowsMax="12"
                label="Auxiliary data (negative weight)" defaultValue=""
                margin="normal"
            />
            <TextField
                id="metadata" fullWidth multiline rowsMax="4"
                label="Comment" defaultValue=""
                margin="normal"
            />
            </Grid>
            </Grid>
        </form>)
    }
}

export default ControllerAddForm;
