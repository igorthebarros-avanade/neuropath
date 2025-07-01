import { ChangeEvent, Dispatch, SetStateAction } from "react"

type Props = {
    label?: string
    setValue: Dispatch<SetStateAction<string>>
    value: string
}

const container = `border border-a-orange bg-a-darkGray px-4 py-1 rounded-lg w-full`
const label = `inline-block text-[12px] w-full`
const input = `h-[100px] pl-2 w-full`

export default function TextArea(props: Props){
    function handleChange(e: ChangeEvent<HTMLTextAreaElement>){
        props.setValue(e.target.value)
    }

    return (
        <div className={container}>
            {props.label ?
                <label className={label} htmlFor={props.label.replaceAll(' ', '')}>
                    {props.label}
                </label>
            : <></>}

            <textarea className={input} id={props.label?.replaceAll(' ', '') || ''} maxLength={500} onChange={handleChange} required style={props.label ? {} : {paddingTop: '.5rem'}} value={props.value}/>
        </div>
    )
}