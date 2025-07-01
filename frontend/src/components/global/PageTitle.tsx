type Props = {
    text: string
}

const title = `font-bold mb-8 text-[30px]`

export default function PageTitle(props: Props){
    return (
        <h1 className={title}>{props.text}</h1>
    )
}