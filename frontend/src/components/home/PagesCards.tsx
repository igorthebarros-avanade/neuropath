import pagesCardsData from "@/src/domain/constants/pagesCardsData";
import PageCard from "./PagesCards/PageCard";

const container = `flex flex-wrap justify-between pb-8`

export default function PagesCards(){
    return(
        <section className={container}>
            {pagesCardsData.map(cardData =>
                <PageCard cardData={cardData} key={cardData.title}/>
            )}
        </section>
    )
}