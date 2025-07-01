import { Dispatch, SetStateAction, useRef } from "react"

type Props = {
    name: string
    options: {
        text: string
        value: string
    }[]
    setValue: Dispatch<SetStateAction<string>>
    value: string
}

const container = `flex items-center gap-8`
const inputContainer = `cursor-pointer flex items-center`
const button = `cursor-pointer scale-[120%]`
const text = `cursor-pointer pl-2 text-[16px]`

export default function Radio(props: Props){
    return (
        <div className={container}>
            {props.options.map(opt => {
                return (
                    <div className={inputContainer} key={opt.value + new Date().getTime()} onClick={() => props.setValue(opt.value)}>
                        <input className={button} defaultChecked={opt.value == props.value} id={opt.value} name={props.name} type="radio" value={opt.value}/>
                        <label className={text} htmlFor={opt.value}>{opt.text}</label>
                    </div>
                )
            })}
        </div>
    )
}