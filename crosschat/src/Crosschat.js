import React from 'react';
import { Switch, Route } from 'react-router-dom';
import Chat from "./Chat";
import DataItem from "./DataItem";
import Navigation from "./Navigation";


class Crosschat extends React.Component {
    render() {
        return(
            <div id='app'>
                <Navigation />
                <Switch>
                    <Route exact path='/' component={Chat}></Route>
                    <Route exact path='/document/:dataset/:id' component={DataItem}></Route>
                </Switch>
            </div>
        );
    }
}


export default Crosschat;

