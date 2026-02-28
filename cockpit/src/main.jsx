import { h, render } from 'preact';
import HologramPreact from './HologramPreact.jsx';
import './styles.css';

const App = () => h(HologramPreact, {});

render(h(App, {}), document.getElementById('app'));
