import React from 'react';
import TextField from '@material-ui/core/TextField';
import Grid from '@material-ui/core/Grid';


/** a chat message with a response provided by the server **/
class ControllerDeltaForm extends React.Component {
    render() {
        return(<form autoComplete="off">
                <Grid container spacing={1}>
                    <Grid item xs={12}>
                        <TextField id="query-id" autoFocus fullWidth multiline rowsMax={8}
                                   value={this.props.query_id}
                                   onInput={(e) => this.props.update("query_id", e.target.value)}
                                   label="Query id" margin="normal"/>
                        <TextField id="query-expected" fullWidth rowsMax={1}
                                   value={this.props.expected_id}
                                   onInput={(e) => this.props.update("expected_id", e.target.value)}
                                   label="Expected identifier" margin="normal"/>
                    </Grid>
                </Grid>
            </form>
        )
    }
}

export default ControllerDeltaForm;

