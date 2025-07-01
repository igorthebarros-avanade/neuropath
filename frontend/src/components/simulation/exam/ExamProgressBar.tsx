type Props = {
    currentIndex: number
    questionsNumber: number
}

const container = `mb-2`
const text = `mb-1 text-[14px] text-end w-full`
const barContainer = `bg-a-gray h-[10px] rounded-full w-full`
const bar = `bg-a-orange h-full rounded-full w-[0%]`

export default function ExamProgressBar(props: Props){
    return (
        <section className={container}>
            {props.currentIndex < props.questionsNumber ?
                <p className={text}>
                    {props.currentIndex + 1}/{props.questionsNumber}
                </p>
            :
                <p className={text}>
                    Completed!
                </p>
            }
            

            <div className={barContainer}>
                <div className={bar} style={{width: `${(props.currentIndex / props.questionsNumber) * 100}%`}}></div>
            </div>
        </section>
    )
}