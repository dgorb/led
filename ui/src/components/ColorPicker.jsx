import React, {useState, useEffect} from 'react';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';
import Slider from '@material-ui/core/Slider';
import {CirclePicker} from 'react-color';
import {HSVtoRGB, RGBtoHEX, RGBtoHSV, coordsToHSV, HSVToCoords, distance} from '../scripts/utils.js';

// TODO: calculate dynamically based on image/img element dimensions?
const D = 250; // Color wheel image width/height
const R = D / 2; // Color wheel "radius", half of image
                 // (assuming that the color wheel takes up the whole image)

export default function ColorPicker(props) {
    const [color, setColor] = useState(props.color);
    const [brightness, setBrightness] = useState(1);
    const [pageX, setPageX] = useState(0);
    const [pageY, setPageY] = useState(0);

    useEffect(() => {
       setWheelPosition(color);
    }, [])

    useEffect(() => {
        if (color.hex !== props.color.hex) {
            setColor(props.color);
            setWheelPosition(props.color);
        }
    }, [props.color])

    const setWheelPosition = (color) => {
        setBrightness(color.hsv[2]);
        const initCursorCoords = HSVToCoords(color.hsv, R);
        setPageX(initCursorCoords[0]);
        setPageY(initCursorCoords[1]);
    }

    const setColorFromRGB = (rgb) => {
        let hsv = RGBtoHSV(rgb);
        let hex = RGBtoHEX(rgb);

        props.setColor({
            rgb: rgb,
            hsv: hsv,
            hex: hex,
        });

        setBrightness(hsv[2]);

        let initCursorCoords = HSVToCoords(hsv, R);
        setPageX(initCursorCoords[0]);
        setPageY(initCursorCoords[1]);
    }

    const onMouseMove = (e) => {
        // Only pick color when pressing the left mouse button
        if (e.buttons == 1 || e.type == 'click') {
            let clr = colorFromCoords(
                e.pageX - e.target.offsetLeft,
                e.pageY - e.target.offsetTop,
            );
            setColor(clr);
            setPageX(e.pageX);
            setPageY(e.pageY);
            props.onChange(clr, e);
        }
    }

    const onTouch = (e) => {
        let clr = colorFromCoords(
            e.touches[0].pageX - e.target.offsetLeft,
            e.touches[0].pageY - e.target.offsetTop
        );
        setColor(clr);
        setPageX(e.touches[0].pageX);
        setPageY(e.touches[0].pageY);
        props.onChange(clr,  e);
    }

    const onBrightnessChange = (e, value) => {
        if (value != brightness) {
            setBrightness(value);

            let hsv = [color.hsv[0], color.hsv[1], value];
            let rgb = HSVtoRGB(color.hsv[0], color.hsv[1], value);
            let hex = RGBtoHEX(rgb);
            let clr = {
                hsv: hsv,
                rgb: rgb,
                hex: hex,
            }
            setColor(clr)
            props.onChange(clr, e);
        }
    }

    const colorFromCoords = (x, y) => {
        let d = distance(R, x, y);
        if (d <= R) { // Only calculate color if we're within the color wheel
            const hsv = coordsToHSV(x, y, R);
            const rgb = HSVtoRGB(hsv[0], hsv[1], brightness);
            const hex = RGBtoHEX(rgb);
            return {
                hsv: hsv,
                rgb: rgb,
                hex: hex,
            }
        } else {
            return color;
        }
    }

    return (
        <div style={{width: window.innerWidth, backgroundColor: "white", paddingLeft: "10px", paddingRight: "10px"}}>
            <img className="nodrag" width="250px" height="250px" src="/color-wheel.png"
                onClick={onMouseMove}
                onMouseMove={onMouseMove}
                onTouchMove={onTouch}
                onTouchStart={onTouch}
            />
            <BrightnessSlider value={brightness} onChange={onBrightnessChange} />
            <br />
            <ColorDisplay color={color} />
            <Cursor x={pageX} y={pageY} />
        </div>
    )
}

function BrightnessSlider(props) {
    const handleChange = (event, val) => {
        props.onChange(event, val);
    }

    return (
        <div style={{width: "90%", backgroundColor: "white", paddingRight: "3%"}}>
            <Typography id="continuous-slider" gutterBottom>
                Brightness
            </Typography>
            <Slider
                value={props.value}
                onChange={handleChange}
                min={0.0}
                max={1.0}
                step={0.01}
                aria-labelledby="continuous-slider"
            />
        </div>
    )
}

function ColorDisplay(props) {
    const [detailsVisible, setDetailsVisible] = useState(false);

    const toggleDetails = () => {
        setDetailsVisible(!detailsVisible);
    }

    return (
        <div style={{width: window.innerWidth, backgroundColor: "white"}} onClick={toggleDetails}>
            <CirclePicker style={{backgroundColor: "white", marginLeft: "10px"}} colors={[props.color.hex]} />
            <br />
            {detailsVisible && <Typography variant="overline" display="block" gutterBottom>
                HSV: {props.color.hsv[0]}, {props.color.hsv[1]}, {props.color.hsv[2]} <br />
                RGB: {props.color.rgb[0]}, {props.color.rgb[1]}, {props.color.rgb[2]} <br />
                Hex: {props.color.hex}
            </Typography> }
        </div>
    )
}

function Cursor(props) {
    const [x, setX] = useState(props.x);
    const [y, setY] = useState(props.y);

    useEffect(() => {
        let d = distance(R, props.x, props.y);
        if (d <= R + 10) {
            setX(props.x);
            setY(props.y);
        }
    }, [props.x, props.y]);

    return (
        <div className='nodrag' style={{position: "absolute", top: y, left: x, cursor: "default"}}>
            <div className='picker-cursor nodrag'></div>
        </div>
    )
}
