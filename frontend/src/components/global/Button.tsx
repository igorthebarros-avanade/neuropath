import { ReactNode } from "react"

type Props = {
    children?: ReactNode
    isDisabled?: boolean
    isSecondary?: boolean
    isSubmit?: boolean
    onClick?: Function
    width?: string
}

const button = `border-2 border-a-orange cursor-pointer px-4 py-2 rounded-lg
active:scale-[98%]
disabled:border-a-darkOrange disabled:cursor-default disabled:scale-[98%]`
const buttonPrimary = `bg-a-orange
disabled:bg-a-darkOrange`
const buttonSecondary = `bg-a-darkGray`

export default function Button(props: Props){
    return (
        <button className={`${button} ${props.isSecondary ? buttonSecondary : buttonPrimary}`} disabled={props.isDisabled} onClick={() => {if(props.onClick) props.onClick()}} style={props.width ? {width: props.width} : {}} type={props.isSubmit ? 'submit' : 'button'}>
            {props.children}
        </button>
    )
}