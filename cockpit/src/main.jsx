import { h, render } from 'preact';
import HologramPreact from './HologramPreact.jsx';
import './styles.css';

const App = () => h('div', { style: { padding: 12 } }, h(HologramPreact, {}));

render(h(App, {}), document.getElementById('app'));
