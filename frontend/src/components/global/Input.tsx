import { ChangeEvent, Dispatch, SetStateAction } from "react"

type Props = {
    isNumber?: boolean
    label: string
    setValue: Dispatch<SetStateAction<string>>
    value: string
}

const container = `border border-a-orange bg-a-darkGray px-4 py-1 rounded-lg w-full`
const label = `inline-block text-[12px] w-full`
const input = `pl-2 w-full`

export default function Input(props: Props){
    function handleChange(e: ChangeEvent<HTMLInputElement>){
        if(props.isNumber){
            props.setValue(e.target.value.replaceAll(/\D/g, '').substring(0, 2))
        }else{
            props.setValue(e.target.value)
        }
    }

    return (
        <div className={container}>
            <label className={label} htmlFor={props.label.replaceAll(' ', '')}>
                {props.label}
            </label>

            <input className={input} id={props.label.replaceAll(' ', '')} maxLength={255} onChange={handleChange} required value={props.value}/>
        </div>
    )
}