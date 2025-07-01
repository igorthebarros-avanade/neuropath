import PageCardData from "@/src/domain/types/PageCardData"
import Link from "next/link"

type Props = {
    cardData: PageCardData
}

const container = `bg-linear-to-tr from-a-darkGray from-75% to-a-darkOrange border border-a-orange px-2 py-4 mb-4 rounded-lg shadow-a-orange shadow-sm w-full
hover:shadow-lg
sm:w-[calc(50%_-_16px)]
md:w-[calc(25%_-_16px)]`
const title = `font-bold mb-3 text-[20px]`
const description = `text-[14px]`

export default function PageCard(props: Props){
    return(
        <Link className={container} href={props.cardData.link}>
            <h2 className={title}>{props.cardData.title}</h2>
            <p className={description}>{props.cardData.description}</p>
        </Link>
    )
}