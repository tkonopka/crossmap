import React from 'react';
import Grid from '@material-ui/core/Grid';
import TextField from '@material-ui/core/TextField';
import Box from '@material-ui/core/Box';


/**
 * A Form with several textboxes.
 * Used to compose a user query with primary data and auxiliary fields.
 */
class ChatQueryBox extends React.Component {
    constructor(props) {
        super(props);
        this.setText = this.setText.bind(this);
        this.state = {data: "", aux_neg: ""}
    }

    /** transfer content of textbox into object state **/
    setText(e, key) {
        let obj = {};
        obj[key] = e.target.value;
        this.setState(obj);
        console.log("state for key "+key+" "+this.state[key])
    }

    render() {
        let neg_visibility = "hidden";
        if (this.props.extended || this.state.aux_neg !== "") {
            neg_visibility = "visible"
        }
        console.log("Rendering extended state: "+this.props.extended + " visibility: "+neg_visibility);
        return(<form autoComplete="off">
            <Grid container spacing={1}>
                <Grid item xs={12}>
                    <TextField id="query-data" fullWidth multiline rowsMax={8} onInput={(e) => this.setText(e, "data")}
                               label="Query" defaultValue="" margin="normal"/>
                    <Box visibility={neg_visibility}>
                        <TextField id="query-aux-neg" fullWidth multiline rowsMax={8}
                                   label="Auxiliary data (negative weight)" defaultValue="" margin="normal"
                        />
                    </Box>
                </Grid>
            </Grid>
            </form>
        )
    }
}

export default ChatQueryBox;
