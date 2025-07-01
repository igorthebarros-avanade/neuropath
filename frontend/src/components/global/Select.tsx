import { Dispatch, SetStateAction, useState } from "react"

type Props = {
    label: string
    options: {
        text: string
        value: string
    }[]
    setValue: Dispatch<SetStateAction<string>>
    value: string
}

const container = `bg-a-darkGray cursor-pointer relative w-full`
const selectedOptionContainer = `border border-a-orange px-4 py-1 rounded-t-lg w-full`
const selectedOption = `flex items-center justify-between pb-2 pl-2`
const label = `cursor-pointer text-[12px] w-full`
const options = `absolute bg-a-darkGray border border-a-orange left-0 rounded-b-lg top-full w-full z-20`
const option = `px-4 py-2 text-[14px]
hover:bg-a-gray hover:text-a-lightGray`

export default function Select(props: Props){  
    const [showOptions, setShowOptions] = useState(false)

    return (
        <div className={container}>
            <div className={`${selectedOptionContainer} ${showOptions ? '' : 'rounded-b-lg'}`} onClick={() => setShowOptions(!showOptions)}>
                <label className={label}>
                    {props.label}
                </label>

                <div className={selectedOption}>
                    <p>{props.options.find(i => i.value == props.value)?.text || ''}</p>
                    {showOptions ?
                        <i className="ri-arrow-up-s-line"></i>
                    :
                        <i className="ri-arrow-down-s-line"></i>
                    }
                </div>
            </div>

            {showOptions ?
                <div className={options} onClick={() => setShowOptions(false)}>
                    {props.options.map(opt =>
                        <p className={option} key={opt.value} onClick={() => props.setValue(opt.value)}>
                            {opt.text}
                        </p>
                    )}
                </div>
            : <></>}
        </div>
    )
}