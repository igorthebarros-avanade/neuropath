type Props = {
    text?: string
}

const container = `bg-[#333333ee] fixed flex h-screen items-center justify-center left-0 top-0 w-screen z-50`
const content = `flex flex-col gap-2 items-center`
const spinner = `animate-spin bg-transparent border-t-2 border-a-orange h-[80px] rounded-full w-[80px]`
const text = `text-[14px]`

export default function Loading(props: Props){
    return (
        <section className={container}>
            <div className={content}>
                <div className={spinner}></div>
                <p className={text}>{props.text || ''}</p>
            </div>
        </section>
    )
}