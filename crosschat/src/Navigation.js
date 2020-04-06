import React from 'react';
import {NavLink} from "react-router-dom";

class Navigation extends React.Component {
    render() {
        return(
            <nav>
                <ul>
                    <li><NavLink to='/'>Home</NavLink></li>
                    <li><NavLink to='/about'>About</NavLink></li>
                </ul>
            </nav>
        )
    }
}


export default Navigation;

